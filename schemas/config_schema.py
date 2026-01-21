from typing import Optional, List, Literal
from pydantic import BaseModel, model_validator


class ConfigSchema(BaseModel):
    algorithm: str                              # required
    #data_range_X: tuple[int, int]                 # required
    #data_range_y: tuple[int, int]
    data_range_X: str  # required
    data_range_y: str

    row_range: Optional[tuple[int, int]] = None

    missing_data: Optional[
        Literal["drop", "mean", "median", "most_frequent", "none"]
    ] = None

    impute_columns: Optional[List[str]] = None

    order_encoding: Optional[bool] = None

    test_size: Optional[float] = None

    scaling: Optional[
        Literal["none", "standardization", "normalization"]
    ] = None

    @model_validator(mode="after")
    def validate_imputation_config(self):
        """
        Ensures missing_data and impute_columns are consistent:
        - Both must be provided, or neither
        - If provided, impute_columns cannot be empty
        """
        if (self.missing_data is None) != (self.impute_columns is None):
            raise ValueError(
                "missing_data and impute_columns must either both be provided or both be omitted"
            )

        if self.impute_columns is not None and len(self.impute_columns) == 0:
            raise ValueError("impute_columns cannot be empty")

        return self