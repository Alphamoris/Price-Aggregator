from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserCreate
from app.utils.exceptions import AuthenticationError, NotFoundError, ValidationError
from app.utils.logging import get_logger
from app.utils.security import hash_password, verify_password

logger = get_logger(__name__)


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user(self, user_data: UserCreate) -> User:
        existing_query = select(User).where(
            (User.username == user_data.username) | (User.email == user_data.email)
        )
        result = await self.db.execute(existing_query)
        existing = result.scalar_one_or_none()

        if existing:
            if existing.username == user_data.username:
                raise ValidationError(message="Username already exists")
            raise ValidationError(message="Email already exists")

        hashed_pw = hash_password(user_data.password)

        user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_pw
        )

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        logger.info("user_created", user_id=user.id, username=user.username)
        return user

    async def authenticate_user(self, username: str, password: str) -> User:
        query = select(User).where(User.username == username)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            raise AuthenticationError(message="Invalid username or password")

        if not verify_password(password, user.hashed_password):
            raise AuthenticationError(message="Invalid username or password")

        if not user.is_active:
            raise AuthenticationError(message="User account is disabled")

        logger.info("user_authenticated", user_id=user.id, username=user.username)
        return user

    async def get_user_by_id(self, user_id: int) -> User:
        query = select(User).where(User.id == user_id)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundError(message="User not found")

        return user

    async def get_user_by_username(self, username: str) -> User:
        query = select(User).where(User.username == username)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundError(message="User not found")

        return user
