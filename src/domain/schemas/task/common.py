from datetime import datetime

from pydantic import BaseModel

from domain.enums.status_type import StatusType


class StatusRetriveDTO(BaseModel):
    id: int
    name: str
    type: StatusType
    color: str

    class Config:
        from_attributes = True
        use_enum_values = True


class SprintRetriveDTO(BaseModel):
    id: int
    name: str
    started_at: datetime
    ended_at: datetime
    active: bool

    class Config:
        from_attributes = True


class CategoryRetriveDTO(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class TagRetrieveDTO(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class SubtaskRetrieveDTO(BaseModel):
    id: int
    name: str
    completed: bool

    class Config:
        from_attributes = True

