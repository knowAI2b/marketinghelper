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
    """创建 users 与 sessions 表。"""
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
        """)
        conn.commit()
    finally:
        conn.close()


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
