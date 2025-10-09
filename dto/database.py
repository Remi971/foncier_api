from enum import Enum

class DatabaseTypeEnum(Enum):
    SUPABASE = "supabase"
    POSTGRESQL = "postgresql"
    SQLITE = "sqlite"