from flask import Blueprint, redirect, request, flash
from services.backup_service import create_backup, restore_backup, reset_database
from core.extensions import db
import os

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.route("/backup")
def backup():
    path = create_backup()
    flash(f"Backup criado: {path}", "success")
    return redirect("/configuracoes")

@admin_bp.route("/reset", methods=["POST"])
def reset():
    confirm = request.form.get("confirm")
    if confirm != "YES":
        flash("Confirmação inválida", "error")
        return redirect("/configuracoes")
    reset_database(db)
    flash("Banco resetado!", "success")
    return redirect("/configuracoes")

@admin_bp.route("/restore", methods=["POST"])
def restore():
    file = request.files.get("file")
    if not file:
        flash("Nenhum arquivo enviado", "error")
        return redirect("/configuracoes")
    os.makedirs("backups", exist_ok=True)
    path = os.path.join("backups", file.filename)
    file.save(path)
    restore_backup(path)
    flash("Backup restaurado!", "success")
    return redirect("/configuracoes")
