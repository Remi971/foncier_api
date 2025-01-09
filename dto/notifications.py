from enum import Enum

class NotificationsTypeEnum(Enum):
    DATA = "data"
    POTENTIEL = "potentiel"
    ENVELOPPE = "enveloppe"
    
class NotificationsStatusEnum(Enum):
    PENDING = "pending"
    ERROR = "error"
    SUCCESS = "success"
    
class NotificationsState(Enum):
    CREATION = "creation"
    UPDATE = "update"
    DELETE = "delete"