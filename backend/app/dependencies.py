from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.user import User
from app.services.user_service import UserService
from app.utils.security import decode_access_token
from app.utils.exceptions import AuthenticationError, AuthorizationError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    token_data = decode_access_token(token)
    
    if token_data.user_id is None:
        raise AuthenticationError(message="Invalid token")
    
    user_service = UserService(db)
    user = await user_service.get_user_by_id(token_data.user_id)
    
    if not user.is_active:
        raise AuthenticationError(message="User account is disabled")
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    if not current_user.is_active:
        raise AuthenticationError(message="Inactive user")
    return current_user


async def get_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    if not current_user.is_admin:
        raise AuthorizationError(message="Admin access required")
    return current_user
