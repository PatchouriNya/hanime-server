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
            created_at TEXT NOT NULL,
            user_type INTEGER DEFAULT 10,
            status INTEGER DEFAULT 10
        )
        """)
        await conn.commit()

        # v4.0.0: 旧表迁移——补充 user_type / status 列（10=普通用户, 20=管理员）
        try:
            await conn.execute("ALTER TABLE users ADD COLUMN user_type INTEGER DEFAULT 10")
        except Exception:
            pass  # 列已存在
        try:
            await conn.execute("ALTER TABLE users ADD COLUMN status INTEGER DEFAULT 10")
        except Exception:
            pass  # 列已存在

        # 检查表是否为空
        cursor = await conn.execute("SELECT COUNT(*) FROM users")
        row = await cursor.fetchone()
        if row[0] == 0:
            now = datetime.now(timezone.utc).isoformat()
            default_users = [
                ("admin", pbkdf2_sha256.hash("666666"), now, 20, 10),  # admin 为管理员
                ("lib", pbkdf2_sha256.hash("666666"), now, 10, 10),
            ]
            await conn.executemany(
                "INSERT INTO users (username, password_hash, created_at, user_type, status) VALUES (?, ?, ?, ?, ?)",
                default_users,
            )
            await conn.commit()
            logger.info("已初始化默认用户: admin(管理员), lib")

        # v4.0.0: 旧数据中 admin 提升为管理员（若 user_type 列刚迁移为默认 10）
        await conn.execute(
            "UPDATE users SET user_type = 20 WHERE username = 'admin' AND user_type < 20"
        )
        await conn.commit()


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
    user_info = {"username": username, "db_type": db_type, "db_user_id": db_user_id}
    # v4.0.0: 附加用户角色（user_type: 10=普通用户, 20=管理员）
    try:
        if db_type == "cloud" and db_user_id:
            from app.services.mysql_user_service import mysql_user_service
            user_type = await mysql_user_service.get_user_type(db_user_id)
            user_info["user_type"] = user_type if user_type is not None else 10
        else:
            user_type = await get_user_type(username)
            user_info["user_type"] = user_type if user_type is not None else 10
    except Exception as e:
        logger.warning(f"获取用户角色失败: {e}")
        user_info["user_type"] = 10
    return user_info


async def get_user_type(username: str) -> Optional[int]:
    """获取用户角色（本地 SQLite）：10=普通用户, 20=管理员"""
    try:
        async with aiosqlite.connect(DB_PATH) as conn:
            cursor = await conn.execute(
                "SELECT user_type FROM users WHERE username = ?", (username,)
            )
            row = await cursor.fetchone()
        return row[0] if row else None
    except Exception as e:
        logger.error(f"获取用户角色失败: {e}")
        return None


async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """管理员权限依赖：user_type >= 20"""
    if user.get("user_type", 10) < 20:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限",
        )
    return user


async def authenticate_user(username: str, password: str) -> bool:
    """从数据库验证用户名和密码"""
    try:
        async with aiosqlite.connect(DB_PATH) as conn:
            cursor = await conn.execute(
                "SELECT password_hash, status FROM users WHERE username = ?", (username,)
            )
            row = await cursor.fetchone()
        if row is None:
            return False
        # v4.0.0: 禁用/封禁用户不能登录
        if row[1] != 10:
            logger.warning(f"用户已被禁用，拒绝登录: {username}")
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
            cursor = await conn.execute("SELECT username, created_at, user_type, status FROM users ORDER BY created_at")
            rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"获取用户列表失败: {e}")
        return []


# ==================== v4.0.0: 用户管理（管理员） ====================

async def create_user(username: str, password: str, user_type: int = 10) -> bool:
    """创建用户"""
    try:
        password_hash = pbkdf2_sha256.hash(password)
        now = datetime.now(timezone.utc).isoformat()
        async with aiosqlite.connect(DB_PATH) as conn:
            await conn.execute(
                "INSERT INTO users (username, password_hash, created_at, user_type, status) VALUES (?, ?, ?, ?, 10)",
                (username, password_hash, now, user_type)
            )
            await conn.commit()
        return True
    except Exception as e:
        logger.error(f"创建用户失败: {e}")
        return False


async def delete_user(username: str) -> bool:
    """删除用户"""
    try:
        async with aiosqlite.connect(DB_PATH) as conn:
            await conn.execute("DELETE FROM users WHERE username = ?", (username,))
            await conn.commit()
        return True
    except Exception as e:
        logger.error(f"删除用户失败: {e}")
        return False


async def reset_user_password(username: str, new_password: str) -> bool:
    """重置用户密码（管理员操作，不校验旧密码）"""
    try:
        new_hash = pbkdf2_sha256.hash(new_password)
        async with aiosqlite.connect(DB_PATH) as conn:
            await conn.execute(
                "UPDATE users SET password_hash = ? WHERE username = ?",
                (new_hash, username)
            )
            await conn.commit()
        return True
    except Exception as e:
        logger.error(f"重置用户密码失败: {e}")
        return False


async def update_user_status(username: str, user_status: int) -> bool:
    """更新用户状态（10=正常, 20=禁用, 30=封禁）"""
    try:
        async with aiosqlite.connect(DB_PATH) as conn:
            await conn.execute(
                "UPDATE users SET status = ? WHERE username = ?",
                (user_status, username)
            )
            await conn.commit()
        return True
    except Exception as e:
        logger.error(f"更新用户状态失败: {e}")
        return False


async def update_user_type(username: str, user_type: int) -> bool:
    """更新用户角色（10=普通用户, 20=管理员）"""
    try:
        async with aiosqlite.connect(DB_PATH) as conn:
            await conn.execute(
                "UPDATE users SET user_type = ? WHERE username = ?",
                (user_type, username)
            )
            await conn.commit()
        return True
    except Exception as e:
        logger.error(f"更新用户角色失败: {e}")
        return False


async def is_user_active(username: str) -> bool:
    """检查用户是否可用（status=10 正常）"""
    try:
        async with aiosqlite.connect(DB_PATH) as conn:
            cursor = await conn.execute(
                "SELECT status FROM users WHERE username = ?", (username,)
            )
            row = await cursor.fetchone()
        return row is None or row[0] == 10
    except Exception as e:
        logger.error(f"检查用户状态失败: {e}")
        return True
