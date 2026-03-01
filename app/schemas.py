from pydantic import BaseModel
from typing import Optional


class APIConfigBase(BaseModel):
    name: str
    base_url: str
    endpoint: str
    method: str
    headers: Optional[str] = None
    auth_type: Optional[str] = None
    auth_value: Optional[str] = None
    response_mapping: Optional[str] = None
    enabled: bool = True


class APIConfigCreate(APIConfigBase):
    pass


class APIConfig(APIConfigBase):
    id: int

    class Config:
        from_attributes = True