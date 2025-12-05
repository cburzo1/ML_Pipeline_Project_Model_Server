import uuid
from enum import Enum
from typing import Optional, List, Literal
from sqlalchemy import Boolean, Column, Integer, String, BIGINT, JSON, DateTime, func, UniqueConstraint
from database import Base
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.dialects.postgresql import JSON

from pydantic import BaseModel

class UserFlows(Base):
    __tablename__ = 'user_flows'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(BIGINT)
    flow_name = Column(String(128))
    config_json = Column(MutableDict.as_mutable(JSON))
    created_at = Column(DateTime, default=func.now())

    __table_args__ = (UniqueConstraint("user_id", "flow_name"),)