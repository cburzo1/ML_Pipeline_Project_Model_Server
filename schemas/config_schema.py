from typing import Optional, Literal
from pydantic import BaseModel


class ConfigSchema(BaseModel):
    model_config = {
        "validate_assignment": True
    }

    algorithm: str
    data_range_X: str
    data_range_y: str

    row_range: Optional[tuple[int, int]] = None

    missing_data: Optional[
        Literal["mean", "constant", "most_frequent", "median"]
    ] = None

    test_size: Optional[float] = None