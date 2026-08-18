from datetime import datetime
import json
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class DatasetCreate(BaseModel):
    name: str = Field(..., max_length=255)
    category: str = Field(..., max_length=255)
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list, max_length=50)
    sample_count: Optional[int] = Field(default=0, ge=0)


class DatasetResponse(BaseModel):
    id: int
    name: str
    category: str
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    sample_count: int
    created_at: datetime

    @field_validator("tags", mode="before")
    @classmethod
    def parse_tags(cls, value):
        if value is None or value == "":
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                return parsed if isinstance(parsed, list) else [value]
            except json.JSONDecodeError:
                return [item.strip() for item in value.split(",") if item.strip()]
        return list(value)

    model_config = {"from_attributes": True}


class CategoryListResponse(BaseModel):
    categories: List[str]
