import enum


class UserRole(str, enum.Enum):
    MODERATOR = "MODERATOR"
    ADMIN = "ADMIN"


class TicketKind(str, enum.Enum):
    CREATE = "CREATE"
    EDIT = "EDIT"


class TicketStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    BLOCKED = "BLOCKED"
    HARD_BLOCKED = "HARD_BLOCKED"


class FieldSeverity(str, enum.Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class TicketAction(str, enum.Enum):
    CREATED = "CREATED"
    CLAIMED = "CLAIMED"
    RELEASED = "RELEASED"
    APPROVED = "APPROVED"
    BLOCKED = "BLOCKED"
    HARD_BLOCKED = "HARD_BLOCKED"
    AUTO_RETURNED = "AUTO_RETURNED"