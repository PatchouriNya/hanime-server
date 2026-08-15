from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from app.utils.auth import (
    create_access_token, authenticate_user, get_current_user, change_password,
    require_admin, get_all_users, create_user, delete_user,
    reset_user_password, update_user_status, update_user_type
)
from app.config import logger

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str
    db_type: str = "local"  # local 或 cloud


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 86400


class AuthStatusResponse(BaseModel):
    authenticated: bool
    username: str = ""


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    if request.db_type == "cloud":
        # 云数据库（MySQL）认证
        from app.services.mysql_user_service import mysql_user_service
        try:
            success, user_id = await mysql_user_service.authenticate_user(request.username, request.password)
            if success:
                access_token = create_access_token(data={
                    "sub": request.username,
                    "db_type": "cloud",
                    "db_user_id": user_id
                })
                logger.info(f"用户登录成功(cloud): {request.username}")
                return LoginResponse(access_token=access_token)
        except Exception as e:
            logger.error(f"MySQL认证异常: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="云数据库连接失败，请稍后重试",
            )
    else:
        # 本地数据库（SQLite）认证
        if await authenticate_user(request.username, request.password):
            access_token = create_access_token(data={"sub": request.username, "db_type": "local"})
            logger.info(f"用户登录成功(local): {request.username}")
            return LoginResponse(access_token=access_token)

    logger.warning(f"登录失败，用户名或密码错误: {request.username}")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="用户名或密码错误",
        headers={"WWW-Authenticate": "Bearer"},
    )


@router.get("/auth/status", response_model=AuthStatusResponse)
async def get_auth_status(user: dict = Depends(get_current_user)):
    # v4.0.0: 返回用户角色（10=普通用户, 20=管理员）
    return AuthStatusResponse(authenticated=True, username=user["username"])


@router.get("/auth/me")
async def get_auth_me(user: dict = Depends(get_current_user)):
    """获取当前用户信息（含角色）"""
    return {
        "authenticated": True,
        "username": user["username"],
        "user_type": user.get("user_type", 10),
        "is_admin": user.get("user_type", 10) >= 20,
        "db_type": user.get("db_type", "local")
    }


# ==================== v4.0.0: 用户管理（仅管理员） ====================

class CreateUserRequest(BaseModel):
    username: str
    password: str
    user_type: int = 10  # 10=普通用户, 20=管理员


class ResetPasswordRequest(BaseModel):
    new_password: str


class UpdateStatusRequest(BaseModel):
    status: int  # 10=正常, 20=禁用, 30=封禁


class UpdateRoleRequest(BaseModel):
    user_type: int  # 10=普通用户, 20=管理员


@router.get("/users")
async def admin_list_users(user: dict = Depends(require_admin)):
    """获取用户列表（管理员）"""
    db_type = user.get("db_type", "local")
    if db_type == "cloud":
        from app.services.mysql_user_service import mysql_user_service
        users = await mysql_user_service.list_users()
    else:
        users = await get_all_users()
    return {"success": True, "users": users}


@router.post("/users")
async def admin_create_user(request: CreateUserRequest, user: dict = Depends(require_admin)):
    """创建用户（管理员）"""
    if len(request.username) < 3 or len(request.password) < 6:
        raise HTTPException(status_code=400, detail="用户名至少3位，密码至少6位")
    db_type = user.get("db_type", "local")
    if db_type == "cloud":
        from app.services.mysql_user_service import mysql_user_service
        success = await mysql_user_service.create_user(request.username, request.password, request.user_type)
    else:
        success = await create_user(request.username, request.password, request.user_type)
    if not success:
        raise HTTPException(status_code=500, detail="创建用户失败（用户名可能已存在）")
    logger.info(f"管理员 {user['username']} 创建用户: {request.username}")
    return {"success": True, "message": "用户创建成功"}


@router.delete("/users/{username}")
async def admin_delete_user(username: str, user: dict = Depends(require_admin)):
    """删除用户（管理员）"""
    if username == user["username"]:
        raise HTTPException(status_code=400, detail="不能删除当前登录的账号")
    db_type = user.get("db_type", "local")
    if db_type == "cloud":
        from app.services.mysql_user_service import mysql_user_service
        ld_user_id = await mysql_user_service.get_user_id_by_username(username)
        if not ld_user_id:
            raise HTTPException(status_code=404, detail="用户不存在")
        success = await mysql_user_service.delete_user(ld_user_id)
    else:
        success = await delete_user(username)
    if not success:
        raise HTTPException(status_code=500, detail="删除用户失败")
    logger.info(f"管理员 {user['username']} 删除用户: {username}")
    return {"success": True, "message": "用户已删除"}


@router.put("/users/{username}/password")
async def admin_reset_password(username: str, request: ResetPasswordRequest, user: dict = Depends(require_admin)):
    """重置用户密码（管理员）"""
    if len(request.new_password) < 6:
        raise HTTPException(status_code=400, detail="密码至少6位")
    db_type = user.get("db_type", "local")
    if db_type == "cloud":
        from app.services.mysql_user_service import mysql_user_service
        ld_user_id = await mysql_user_service.get_user_id_by_username(username)
        if not ld_user_id:
            raise HTTPException(status_code=404, detail="用户不存在")
        success = await mysql_user_service.reset_user_password(ld_user_id, request.new_password)
    else:
        success = await reset_user_password(username, request.new_password)
    if not success:
        raise HTTPException(status_code=500, detail="重置密码失败")
    logger.info(f"管理员 {user['username']} 重置用户密码: {username}")
    return {"success": True, "message": "密码已重置"}


@router.put("/users/{username}/status")
async def admin_update_status(username: str, request: UpdateStatusRequest, user: dict = Depends(require_admin)):
    """更新用户状态（管理员）：10=正常, 20=禁用, 30=封禁"""
    if username == user["username"]:
        raise HTTPException(status_code=400, detail="不能禁用当前登录的账号")
    if request.status not in (10, 20, 30):
        raise HTTPException(status_code=400, detail="状态值无效")
    db_type = user.get("db_type", "local")
    if db_type == "cloud":
        from app.services.mysql_user_service import mysql_user_service
        ld_user_id = await mysql_user_service.get_user_id_by_username(username)
        if not ld_user_id:
            raise HTTPException(status_code=404, detail="用户不存在")
        success = await mysql_user_service.update_user_status(ld_user_id, request.status)
    else:
        success = await update_user_status(username, request.status)
    if not success:
        raise HTTPException(status_code=500, detail="更新状态失败")
    logger.info(f"管理员 {user['username']} 更新用户状态: {username} -> {request.status}")
    return {"success": True, "message": "状态已更新"}


@router.put("/users/{username}/role")
async def admin_update_role(username: str, request: UpdateRoleRequest, user: dict = Depends(require_admin)):
    """更新用户角色（管理员）：10=普通用户, 20=管理员"""
    if username == user["username"]:
        raise HTTPException(status_code=400, detail="不能修改当前登录账号的角色")
    if request.user_type not in (10, 20):
        raise HTTPException(status_code=400, detail="角色值无效")
    db_type = user.get("db_type", "local")
    if db_type == "cloud":
        from app.services.mysql_user_service import mysql_user_service
        ld_user_id = await mysql_user_service.get_user_id_by_username(username)
        if not ld_user_id:
            raise HTTPException(status_code=404, detail="用户不存在")
        success = await mysql_user_service.update_user_type(ld_user_id, request.user_type)
    else:
        success = await update_user_type(username, request.user_type)
    if not success:
        raise HTTPException(status_code=500, detail="更新角色失败")
    logger.info(f"管理员 {user['username']} 更新用户角色: {username} -> {request.user_type}")
    return {"success": True, "message": "角色已更新"}


@router.post("/logout")
async def logout(user: dict = Depends(get_current_user)):
    logger.info(f"用户登出: {user['username']}")
    return {"success": True, "message": "登出成功"}


@router.put("/change-password")
async def change_password_endpoint(
    request: ChangePasswordRequest,
    user: dict = Depends(get_current_user),
):
    username = user["username"]
    db_type = user.get("db_type", "local")

    if db_type == "cloud":
        from app.services.mysql_user_service import mysql_user_service
        db_user_id = user.get("db_user_id")
        if not db_user_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户信息异常")
        if await mysql_user_service.change_password(db_user_id, request.old_password, request.new_password):
            logger.info(f"用户修改密码成功(cloud): {username}")
            return {"success": True, "message": "密码修改成功"}
    else:
        if await change_password(username, request.old_password, request.new_password):
            logger.info(f"用户修改密码成功(local): {username}")
            return {"success": True, "message": "密码修改成功"}

    logger.warning(f"用户修改密码失败（旧密码错误）: {username}")
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="旧密码错误",
    )
