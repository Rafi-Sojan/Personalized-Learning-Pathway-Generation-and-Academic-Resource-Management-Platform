from pydantic import BaseModel, Field


class Page(BaseModel):
    items: list[dict]
    total: int
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
