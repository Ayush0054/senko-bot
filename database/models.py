from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(String, index=True)
    channel_id = Column(String, index=True)
    user_id = Column(String, index=True)
    content = Column(Text)
    timestamp = Column(DateTime)