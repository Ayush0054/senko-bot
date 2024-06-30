from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base, Message
from sqlalchemy.future import select

class MessageStore:
    def __init__(self, database_url: str):
        #URL starts with postgresql+asyncpg://
        if database_url.startswith('postgresql://'):
            database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
        self.engine = create_async_engine(database_url)
        self.SessionLocal = sessionmaker(
            bind=self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def init_db(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def store_message(self, server_id: str, channel_id: str, user_id: str, content: str, timestamp):
        async with self.SessionLocal() as session:
            message = Message(
                server_id=server_id,
                channel_id=channel_id,
                user_id=user_id,
                content=content,
                timestamp=timestamp
            )
            session.add(message)
            await session.commit()

    async def get_recent_messages(self, server_id: str, channel_id: str, limit: int = 10):
        async with self.SessionLocal() as session:
            query = select(Message).filter(
                Message.server_id == server_id,
                Message.channel_id == channel_id
            ).order_by(Message.timestamp.desc()).limit(limit)
            result = await session.execute(query)
            return result.scalars().all()