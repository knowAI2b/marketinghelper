"""SQLite3 用户与会话：注册、登录、登出。密码使用 PBKDF2-HMAC-SHA256。"""
from __future__ import annotations

import hashlib
import secrets
import sqlite3
from pathlib import Path

# 项目根目录下的 data 目录存放 auth.db
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_DIR = PROJECT_ROOT / "data"
DB_PATH = DB_DIR / "auth.db"
UPLOAD_ROOT = DB_DIR / "uploads"

PBKDF2_ITERATIONS = 100_000


def _hash_password(password: str, salt: bytes | None = None) -> tuple[bytes, str]:
    """返回 (salt, stored_string)，stored_string 为 salt_hex:hash_hex。"""
    if salt is None:
        salt = secrets.token_bytes(16)
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )
    stored = f"{salt.hex()}:{key.hex()}"
    return salt, stored


def _verify_password(password: str, stored: str) -> bool:
    salt_hex, hash_hex = stored.split(":", 1)
    salt = bytes.fromhex(salt_hex)
    _, expected = _hash_password(password, salt)
    return secrets.compare_digest(stored, expected)


def _ensure_db_dir() -> None:
    DB_DIR.mkdir(parents=True, exist_ok=True)


def _get_conn() -> sqlite3.Connection:
    _ensure_db_dir()
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """创建 users / sessions / uploaded_images 等表。"""
    conn = _get_conn()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            CREATE INDEX IF NOT EXISTS ix_sessions_user_id ON sessions(user_id);

            CREATE TABLE IF NOT EXISTS uploaded_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NULL,
                path TEXT NOT NULL,  -- 相对路径，如 2026/02/11/uuid.png
                original_name TEXT,
                content_type TEXT,
                size_bytes INTEGER,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            CREATE INDEX IF NOT EXISTS ix_uploaded_images_user_id ON uploaded_images(user_id);
        """)
        conn.commit()
    finally:
        conn.close()


def save_uploaded_image_bytes(
    data: bytes,
    original_name: str,
    content_type: str | None,
    user_id: int | None = None,
) -> dict:
    """将上传的图片字节落盘到 data/uploads/{yyyy}/{mm}/{dd}/uuid.ext，并写入 uploaded_images 表。"""
    from datetime import datetime
    import uuid
    import os

    _ensure_db_dir()
    now = datetime.utcnow()
    yyyy = f"{now.year:04d}"
    mm = f"{now.month:02d}"
    dd = f"{now.day:02d}"

    # 目录：data/uploads/yyyy/mm/dd
    folder = UPLOAD_ROOT / yyyy / mm / dd
    folder.mkdir(parents=True, exist_ok=True)

    # 扩展名
    _, ext = os.path.splitext(original_name or "")
    ext = (ext or "").lower()
    if not ext or len(ext) > 10:
        ext = ".bin"

    filename = f"{uuid.uuid4().hex}{ext}"
    rel_path = f"{yyyy}/{mm}/{dd}/{filename}"
    abs_path = folder / filename

    abs_path.write_bytes(data)

    conn = _get_conn()
    try:
        cur = conn.execute(
            """
            INSERT INTO uploaded_images (user_id, path, original_name, content_type, size_bytes)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, rel_path, original_name, content_type, len(data)),
        )
        conn.commit()
        image_id = cur.lastrowid
    finally:
        conn.close()

    return {
        "id": image_id,
        "path": rel_path,
        "original_name": original_name,
        "content_type": content_type,
        "size_bytes": len(data),
    }


def register(username: str, password: str) -> tuple[bool, str]:
    """
    注册新用户。返回 (成功?, 错误信息或空字符串)。
    """
    if not username or not username.strip():
        return False, "用户名不能为空"
    if not password or len(password) < 6:
        return False, "密码至少 6 位"
    username = username.strip()
    _, stored = _hash_password(password)
    conn = _get_conn()
    try:
        conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, stored),
        )
        conn.commit()
        return True, ""
    except sqlite3.IntegrityError:
        return False, "用户名已存在"
    finally:
        conn.close()


def login(username: str, password: str) -> tuple[bool, str, str | None]:
    """
    登录。返回 (成功?, 错误信息或空字符串, 登录成功时的 token 或 None)。
    """
    if not username or not password:
        return False, "用户名和密码不能为空", None
    username = username.strip()
    conn = _get_conn()
    try:
        row = conn.execute(
            "SELECT id, password_hash FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        if not row:
            return False, "用户名或密码错误", None
        user_id = row["id"]
        if not _verify_password(password, row["password_hash"]):
            return False, "用户名或密码错误", None
        token = secrets.token_urlsafe(32)
        conn.execute(
            "INSERT INTO sessions (token, user_id) VALUES (?, ?)",
            (token, user_id),
        )
        conn.commit()
        return True, "", token
    finally:
        conn.close()


def logout(token: str) -> bool:
    """登出：删除该 token 的会话。"""
    conn = _get_conn()
    try:
        cur = conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def get_user_by_token(token: str) -> dict | None:
    """根据 token 获取用户信息，无效则返回 None。"""
    if not token:
        return None
    conn = _get_conn()
    try:
        row = conn.execute(
            """
            SELECT u.id, u.username, u.created_at
            FROM users u
            JOIN sessions s ON s.user_id = u.id
            WHERE s.token = ?
            """,
            (token,),
        ).fetchone()
        if not row:
            return None
        return {"id": row["id"], "username": row["username"], "created_at": row["created_at"]}
    finally:
        conn.close()
