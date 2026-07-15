from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from app.utils.auth import create_access_token, authenticate_user, get_current_user, change_password
from app.config import logger

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


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
    if await authenticate_user(request.username, request.password):
        access_token = create_access_token(data={"sub": request.username})
        logger.info(f"用户登录成功: {request.username}")
        return LoginResponse(access_token=access_token)
    logger.warning(f"登录失败，用户名或密码错误: {request.username}")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="用户名或密码错误",
        headers={"WWW-Authenticate": "Bearer"},
    )


@router.get("/auth/status", response_model=AuthStatusResponse)
async def get_auth_status(user: dict = Depends(get_current_user)):
    return AuthStatusResponse(authenticated=True, username=user["username"])


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
    if await change_password(username, request.old_password, request.new_password):
        logger.info(f"用户修改密码成功: {username}")
        return {"success": True, "message": "密码修改成功"}
    logger.warning(f"用户修改密码失败（旧密码错误）: {username}")
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="旧密码错误",
    )
