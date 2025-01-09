from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String, TIMESTAMP, text
import uuid

Base = declarative_base()

class Notification(Base):
    __tablename__= 'notifications'
    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False, unique=True, default=uuid.uuid4)
    recipient = Column(String, nullable=False)
    message = Column(String)
    type = Column(String)
    status = Column(String)
    createdAt = Column(TIMESTAMP(timezone=True), nullable=False, default=text('Now()'))
    updatedAt = Column(TIMESTAMP(timezone=True), nullable=False, default=text('Now()'), server_onupdate=text('Now()'))