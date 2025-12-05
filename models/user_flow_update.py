from pydantic import BaseModel
from typing import Optional, Dict, Any

class UserFlowUpdate(BaseModel):
    flow_name: Optional[str] = None
    config_json: Optional[Dict[str, Any]] = None