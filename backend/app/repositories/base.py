from typing import Any, Generic, Sequence, TypeVar
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def get(self, id: Any) -> ModelType | None:
        """Fetch a single record by its primary key."""
        return await self.session.get(self.model, id)

    async def get_multi(self, skip: int = 0, limit: int = 100) -> Sequence[ModelType]:
        """Fetch multiple records with pagination."""
        query = select(self.model).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def create(self, db_obj: ModelType) -> ModelType:
        """Persist a new model instance to the database."""
        self.session.add(db_obj)
        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj

    async def update(
        self, db_obj: ModelType, obj_in: dict[str, Any] | ModelType
    ) -> ModelType:
        """Update an existing model instance."""
        if isinstance(obj_in, dict):
            for field, value in obj_in.items():
                if hasattr(db_obj, field):
                    setattr(db_obj, field, value)
        else:
            for field in self.model.__table__.columns.keys():
                if hasattr(obj_in, field):
                    val = getattr(obj_in, field)
                    setattr(db_obj, field, val)
        self.session.add(db_obj)
        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj

    async def delete(self, id: Any) -> ModelType | None:
        """Physically delete a record from the database."""
        db_obj = await self.get(id)
        if db_obj:
            await self.session.delete(db_obj)
            await self.session.commit()
        return db_obj
