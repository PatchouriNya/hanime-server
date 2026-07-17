import jwt
import aiosqlite
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.hash import pbkdf2_sha256
from app.config import settings, logger

JWT_SECRET_KEY = settings.APP_NAME + "_SECRET_KEY_2026"
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 1440

security = HTTPBearer()

DB_PATH = settings.DB_PATH / "user.db"


async def init_users_db():
    """初始化用户表，若表为空则插入默认用户"""
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """)
        await conn.commit()

        # 检查表是否为空
        cursor = await conn.execute("SELECT COUNT(*) FROM users")
        row = await cursor.fetchone()
        if row[0] == 0:
            now = datetime.now(timezone.utc).isoformat()
            default_users = [
                ("admin", pbkdf2_sha256.hash("666666"), now),
                ("lib", pbkdf2_sha256.hash("666666"), now),
            ]
            await conn.executemany(
                "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
                default_users,
            )
            await conn.commit()
            logger.info("已初始化默认用户: admin, lib")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.PyJWTError as e:
        logger.warning(f"Token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token = credentials.credentials
    payload = verify_token(token)
    username = payload.get("sub")
    db_type = payload.get("db_type", "local")
    db_user_id = payload.get("db_user_id")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    return {"username": username, "db_type": db_type, "db_user_id": db_user_id}


async def authenticate_user(username: str, password: str) -> bool:
    """从数据库验证用户名和密码"""
    try:
        async with aiosqlite.connect(DB_PATH) as conn:
            cursor = await conn.execute(
                "SELECT password_hash FROM users WHERE username = ?", (username,)
            )
            row = await cursor.fetchone()
        if row is None:
            return False
        return pbkdf2_sha256.verify(password, row[0])
    except Exception as e:
        logger.error(f"验证用户失败: {e}")
        return False


async def change_password(username: str, old_password: str, new_password: str) -> bool:
    """验证旧密码后更新为新密码"""
    if not await authenticate_user(username, old_password):
        return False
    try:
        new_hash = pbkdf2_sha256.hash(new_password)
        async with aiosqlite.connect(DB_PATH) as conn:
            await conn.execute(
                "UPDATE users SET password_hash = ? WHERE username = ?",
                (new_hash, username),
            )
            await conn.commit()
        return True
    except Exception as e:
        logger.error(f"修改密码失败: {e}")
        return False


async def get_all_users() -> List[Dict]:
    """获取所有用户列表"""
    try:
        async with aiosqlite.connect(DB_PATH) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute("SELECT username, created_at FROM users ORDER BY created_at")
            rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"获取用户列表失败: {e}")
        return []
