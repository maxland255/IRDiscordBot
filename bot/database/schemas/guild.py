from pydantic import BaseModel


class Guild(BaseModel):
    id: int
    name: str

    # salon de logs
    logs_moderation: int
    logs_server: int

    # tickets system
    # pass

    class Config:
        from_attributes = True
