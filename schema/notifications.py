from pydantic import BaseModel
from dto.notifications import NotificationsStatusEnum, NotificationsTypeEnum

class Notifications(BaseModel):
    message: str
    status: NotificationsStatusEnum
    type: NotificationsTypeEnum
    
class NotificationsModel(Notifications):
    recipient: str
    
class NotificationsMessage(NotificationsModel):
    id: str