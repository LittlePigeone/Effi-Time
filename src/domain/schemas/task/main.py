from datetime import datetime

from pydantic import BaseModel, field_validator

from domain.schemas.task.common import StatusRetriveDTO, SprintRetriveDTO, CategoryRetriveDTO, TagRetrieveDTO, \
    SubtaskRetrieveDTO
from domain.schemas.user.main import UserRetriveDTO


class TaskCreateDTO(BaseModel):
    user_id: int
    name: str
    description: str = ""
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    status_id: int | None = None
    sprint_id: int | None = None
    category_id: int | None = None


class TaskRetrieveDTO(BaseModel):
    id: int
    name: str
    description: str = ""
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    status: StatusRetriveDTO | None = None
    sprint: SprintRetriveDTO | None = None
    category: CategoryRetriveDTO | None = None
    user: UserRetriveDTO | None = None
    tags: list[TagRetrieveDTO] = []
    subtasks: list[SubtaskRetrieveDTO] = []

    @field_validator("subtasks", "tags", mode="before")
    @staticmethod
    def validate_subtask_field(value) -> list:
        return value.all()

    class Config:
        from_attributes = True


class TaskUpdateDTO(TaskCreateDTO):
    id: int