import os
import shutil
from datetime import datetime

DB_PATH = "instance/serviceflow_dev.sqlite3"
BACKUP_DIR = "backups"

def create_backup():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"backup_{timestamp}.sqlite3")
    shutil.copy2(DB_PATH, backup_path)
    return backup_path

def restore_backup(file_path):
    if not os.path.exists(file_path):
        raise Exception("Backup não encontrado")
    shutil.copy2(file_path, DB_PATH)

def reset_database(db):
    db.drop_all()
    db.create_all()
