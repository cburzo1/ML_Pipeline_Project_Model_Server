import uuid
from enum import Enum
from typing import Optional, List, Literal

from pydantic import BaseModel
from sqlalchemy import Boolean, Column, Integer, String, BIGINT, JSON, DateTime, func
from database import Base

class ConfigSchema(BaseModel):
    algorithm: str                              # required
    data_range: tuple[int, int]                 # required

    missing_data: Optional[
        Literal["drop", "mean", "median", "most_frequent", "none"]
    ] = None

    order_encoding: Optional[bool] = None

    test_size: Optional[float] = None

    scaling: Optional[
        Literal["none", "standardization", "normalization"]
    ] = None