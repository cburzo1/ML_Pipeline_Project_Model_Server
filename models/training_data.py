import uuid
from sqlalchemy import Boolean, Column, Integer, String, BIGINT, JSON, DateTime, func, UniqueConstraint, FLOAT
from database import Base
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.dialects.postgresql import JSON


class TrainingData(Base):
    __tablename__ = 'training_data'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    flow_id = Column(String(36))
    feature_vector = Column(MutableDict.as_mutable(JSON))
    label = Column(FLOAT)
    trained_at = Column(DateTime, default=func.now())