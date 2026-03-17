import uuid
from sqlalchemy import Boolean, Column, Integer, String, BIGINT, JSON, DateTime, func, UniqueConstraint
from database import Base
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.dialects.postgresql import JSON


class TrainedModels(Base):
    __tablename__ = 'trained_models'

    id = Column(String(36), primary_key=True, index=True)
    flow_id = Column(String(36))
    model_type = Column(String(128))
    model_path =  Column(String(255))
    metrics_json = Column(MutableDict.as_mutable(JSON))
    trained_at = Column(DateTime, default=func.now())

    __table_args__ = (UniqueConstraint("model_path", name="uq_trainedmodels_model_path"),)