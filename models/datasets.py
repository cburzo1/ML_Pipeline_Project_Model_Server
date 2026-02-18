import uuid
from sqlalchemy import Boolean, Column, Integer, String, BIGINT, JSON, DateTime, func, UniqueConstraint, Text, false, Enum as SQLEnum
from database import Base
from enum import Enum
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.dialects.postgresql import JSON

class DataFormat(str, Enum):
    csv = "csv"

class DataSets(Base):
    __tablename__ = 'datasets'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(BIGINT, nullable=False)
    dataset_name = Column(String(128), nullable=False)
    description = Column(Text)
    format = Column(SQLEnum(DataFormat), nullable=False, default=DataFormat.csv)
    storage_path = Column(String(255), nullable=False)
    row_count = Column(Integer)
    #column_schema = Column(MutableDict.as_mutable(JSON))
    #has_header = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    #deleted_at = Column(DateTime, default=func.now())

    __table_args__ = (
        UniqueConstraint('user_id', 'dataset_name', name='uq_user_dataset_name'),
    )