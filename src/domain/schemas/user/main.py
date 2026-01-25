from pydantic import BaseModel


class UserRetriveDTO(BaseModel):
    id: int
    username: str
    photo_url: str | None = None

    class Config:
        from_attributes = True