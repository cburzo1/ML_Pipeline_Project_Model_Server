from typing import Optional, List, Literal
from pydantic import BaseModel

class ConfigSchema(BaseModel):
    algorithm: str                              # required
    #data_range_X: tuple[int, int]                 # required
    #data_range_y: tuple[int, int]
    data_range_X: str  # required
    data_range_y: str

    missing_data: Optional[
        Literal["drop", "mean", "median", "most_frequent", "none"]
    ] = None

    order_encoding: Optional[bool] = None

    test_size: Optional[float] = None

    scaling: Optional[
        Literal["none", "standardization", "normalization"]
    ] = None