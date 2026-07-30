from pathlib import Path
import sqlite3

# ============================================================
# Project Root
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

# ============================================================
# Database
# ============================================================

DB_PATH = ROOT / "storage" / "database" / "ETH.db"

# ============================================================
# Connection
# ============================================================

def get_connection():
    return sqlite3.connect(DB_PATH)


def get_cursor():
    conn = get_connection()
    return conn, conn.cursor()