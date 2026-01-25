from enum import Enum

class StatusType(Enum):
    new = "Новый"
    in_work = "В работе"
    on_pause = "На паузе"
    closed = "Закрыт"
