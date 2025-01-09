from sqlalchemy import Column, String, TIMESTAMP, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
from dto.users import Roles
import uuid

Base = declarative_base()
class User(Base):
    __tablename__= 'users'
    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False, unique=True, default=uuid.uuid4)
    firstname = Column(String, nullable=False)
    lastname = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False, default=Roles.BASIC.value)
    createdAt = Column(TIMESTAMP(timezone=True), nullable=False, default=text('Now()'))
    updatedAt = Column(TIMESTAMP(timezone=True), nullable=False, default=text('Now()'), server_onupdate=text('Now()'))
    