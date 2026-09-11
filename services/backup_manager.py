"""Serviço de backup e manutenção do banco local do ServiceFlow.

A implementação é intencionalmente simples e robusta para ambientes Flask/SQLite:
- gera ZIP com cópia integral do banco;
- mantém metadados do backup;
- cria backup automático diário sob demanda;
- restaura banco a partir de ZIP validado;
- executa reset seguro dos dados operacionais preservando a conta atual.
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable

from flask import current_app
from sqlalchemy.engine.url import make_url

from models import (
    db,
    Client,
    Event,
    Message,
    MessageThread,
    Notification,
    Service,
    Task,
    ThreadParticipant,
    Transaction,
    User,
)

BACKUP_FOLDER_NAME = "backups"
AUTO_FOLDER_NAME = "automaticos"
MANUAL_FOLDER_NAME = "manuais"
RESTORE_FOLDER_NAME = "restauracoes"
MAX_BACKUP_UPLOAD_BYTES = 10 * 1024 * 1024


def _utc_now() -> datetime:
    return datetime.utcnow()


def _timestamp() -> str:
    return _utc_now().strftime("%Y%m%d_%H%M%S")


def get_database_path() -> Path:
    """Retorna o caminho físico do SQLite configurado no Flask."""
    uri = current_app.config.get("SQLALCHEMY_DATABASE_URI", "")
    url = make_url(uri)
    if url.drivername != "sqlite":
        raise RuntimeError("Backup local disponível apenas para SQLite neste ambiente.")

    database = url.database or ""
    if database in ("", ":memory:"):
        raise RuntimeError("Banco SQLite em memória não pode ser copiado para backup.")

    db_path = Path(database)
    if not db_path.is_absolute():
        db_path = Path(current_app.instance_path) / database
    return db_path.resolve()


def get_backup_root() -> Path:
    root = Path(current_app.instance_path) / BACKUP_FOLDER_NAME
    root.mkdir(parents=True, exist_ok=True)
    return root


def _backup_dir(kind: str) -> Path:
    folder = get_backup_root() / kind
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def create_backup(kind: str = MANUAL_FOLDER_NAME, reason: str = "manual") -> Path:
    """Cria um ZIP contendo uma cópia integral do banco SQLite e metadados."""
    db_path = get_database_path()
    if not db_path.exists():
        raise FileNotFoundError(f"Banco de dados não encontrado: {db_path}")

    destination = _backup_dir(kind) / f"serviceflow_backup_{reason}_{_timestamp()}.zip"
    metadata = {
        "app": "ServiceFlow",
        "version": "sqlite-full-backup-v1",
        "created_at_utc": _utc_now().isoformat(timespec="seconds") + "Z",
        "reason": reason,
        "database_file": db_path.name,
    }

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        copied_db = tmp_path / db_path.name

        # Garante que alterações pendentes sejam gravadas antes da cópia.
        db.session.remove()
        shutil.copy2(db_path, copied_db)

        metadata_path = tmp_path / "metadata.json"
        metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

        with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.write(copied_db, arcname=db_path.name)
            zf.write(metadata_path, arcname="metadata.json")

    return destination


def list_backups(limit: int = 8) -> list[dict]:
    """Lista backups recentes para exibição na tela de segurança."""
    root = get_backup_root()
    files = sorted(root.glob("**/*.zip"), key=lambda p: p.stat().st_mtime, reverse=True)
    items = []
    for path in files[:limit]:
        stat = path.stat()
        items.append(
            {
                "name": path.name,
                "kind": path.parent.name,
                "size_kb": max(1, round(stat.st_size / 1024)),
                "created_at": datetime.fromtimestamp(stat.st_mtime),
            }
        )
    return items


def ensure_daily_backup() -> Path | None:
    """Cria backup automático se não existir um backup das últimas 24 horas."""
    auto_dir = _backup_dir(AUTO_FOLDER_NAME)
    latest = max(auto_dir.glob("*.zip"), key=lambda p: p.stat().st_mtime, default=None)
    if latest:
        latest_time = datetime.fromtimestamp(latest.stat().st_mtime)
        if datetime.now() - latest_time < timedelta(hours=24):
            return None
    return create_backup(kind=AUTO_FOLDER_NAME, reason="automatico_diario")


def _extract_sqlite_from_zip(upload_path: Path) -> Path:
    """Valida o ZIP enviado e retorna o arquivo SQLite extraído."""
    if not zipfile.is_zipfile(upload_path):
        raise ValueError("Envie um arquivo ZIP de backup válido.")

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        with zipfile.ZipFile(upload_path) as zf:
            members = [m for m in zf.namelist() if not m.endswith("/")]
            candidates = [m for m in members if Path(m).suffix.lower() in {".db", ".sqlite", ".sqlite3"}]
            if not candidates:
                raise ValueError("O ZIP não contém um banco SQLite válido.")

            chosen = candidates[0]
            safe_name = Path(chosen).name
            extracted = tmp_path / safe_name
            with zf.open(chosen) as src, extracted.open("wb") as dst:
                total = 0
                while True:
                    chunk = src.read(1024 * 1024)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > MAX_BACKUP_UPLOAD_BYTES:
                        raise ValueError("O banco no backup excede o limite permitido.")
                    dst.write(chunk)

            with extracted.open("rb") as database_file:
                if database_file.read(16) != b"SQLite format 3\x00":
                    raise ValueError("O arquivo extraído não é um banco SQLite válido.")

        persistent = Path(tempfile.mkstemp(prefix="serviceflow_restore_", suffix=extracted.suffix)[1])
        shutil.copy2(extracted, persistent)
        return persistent


def restore_backup(upload_stream, filename: str) -> None:
    """Restaura o banco SQLite a partir de um ZIP de backup."""
    if not filename or not filename.lower().endswith(".zip"):
        raise ValueError("O arquivo de restauração precisa ser um ZIP.")

    content_length = request_content_length(upload_stream)
    if content_length and content_length > MAX_BACKUP_UPLOAD_BYTES:
        raise ValueError("O arquivo de restauração excede o limite permitido.")

    db_path = get_database_path()
    if not db_path.exists():
        raise FileNotFoundError("Banco atual não encontrado para restauração.")

    restore_dir = _backup_dir(RESTORE_FOLDER_NAME)
    uploaded_zip = restore_dir / f"upload_restore_{_timestamp()}.zip"
    upload_stream.save(uploaded_zip)

    extracted_db = _extract_sqlite_from_zip(uploaded_zip)
    try:
        create_backup(kind=RESTORE_FOLDER_NAME, reason="antes_da_restauracao")
        db.session.remove()
        db.engine.dispose()
        shutil.copy2(extracted_db, db_path)
    finally:
        try:
            extracted_db.unlink(missing_ok=True)
        except OSError:
            pass


def request_content_length(upload_stream) -> int | None:
    """Obtém o tamanho declarado pelo upload sem depender de um request global."""
    stream = getattr(upload_stream, "stream", None)
    length = getattr(stream, "content_length", None)
    return length if isinstance(length, int) and length >= 0 else None


def _delete_all(model) -> int:
    count = model.query.count()
    model.query.delete(synchronize_session=False)
    return count


def reset_operational_data(current_user: User) -> dict:
    """Remove dados operacionais preservando tenant, conta atual e acesso ao sistema."""
    if not current_user:
        raise ValueError("Usuário atual não identificado.")

    create_backup(kind=MANUAL_FOLDER_NAME, reason="antes_do_reset")

    # Ordem respeita dependências de chave estrangeira.
    deleted = {
        "notifications": _delete_all(Notification),
        "messages": _delete_all(Message),
        "thread_participants": _delete_all(ThreadParticipant),
        "message_threads": _delete_all(MessageThread),
        "events": _delete_all(Event),
        "tasks": _delete_all(Task),
        "transactions": _delete_all(Transaction),
        "services": _delete_all(Service),
    }

    # Remove clientes depois dos registros que dependem deles.
    deleted["clients"] = _delete_all(Client)

    # Preserva o usuário logado para não derrubar o acesso após o reset.
    deleted["users_removed"] = User.query.filter(User.id != current_user.id).delete(synchronize_session=False)
    current_user.client_id = None
    current_user.status = "active"

    db.session.commit()
    return deleted
