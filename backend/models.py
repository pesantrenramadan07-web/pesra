from datetime import datetime, timezone
from typing import Optional, List, Annotated, Any
from pydantic import BaseModel, Field, BeforeValidator, ConfigDict
from bson import ObjectId


def _validate_object_id(v: Any) -> str:
    if isinstance(v, ObjectId):
        return str(v)
    return str(v)


PyObjectId = Annotated[str, BeforeValidator(_validate_object_id)]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class BaseDocument(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")
    id: Optional[PyObjectId] = Field(default=None, alias="_id")

    @classmethod
    def from_mongo(cls, doc: dict):
        if not doc:
            return None
        return cls(**doc)

    def to_mongo(self) -> dict:
        data = self.model_dump(by_alias=True, exclude_none=True)
        data.pop("_id", None)
        data.pop("id", None)
        return data


# ------------- Master data payloads -------------

class PeriodIn(BaseModel):
    name: str
    hijri_year: str
    start_date: str
    end_date: str
    status: str = "DRAFT"
    is_test: bool = False
    notes: Optional[str] = ""


class SchoolIn(BaseModel):
    code: str
    name: str
    address: Optional[str] = ""
    region: Optional[str] = ""
    contact_person: Optional[str] = ""
    contact_phone: Optional[str] = ""
    status: str = "ACTIVE"


class TeacherIn(BaseModel):
    name: str
    gender: str = "L"
    phone: Optional[str] = ""
    address: Optional[str] = ""
    status: str = "ACTIVE"
    notes: Optional[str] = ""


class DailyBoardIn(BaseModel):
    name: str
    position: str
    phone: Optional[str] = ""
    status: str = "ACTIVE"
    notes: Optional[str] = ""
    school_ids: List[str] = Field(default_factory=list)


class OfficerIn(BaseModel):
    name: str
    position: str
    phone: Optional[str] = ""
    status: str = "ACTIVE"
    notes: Optional[str] = ""


class VehicleIn(BaseModel):
    code: str
    type: str = "ELF_PONDOK"
    capacity: Optional[int] = 0
    status: str = "ACTIVE"
    notes: Optional[str] = ""


class ScheduleIn(BaseModel):
    period_id: str
    school_id: str
    date: str  # YYYY-MM-DD
    start_time: Optional[str] = ""
    end_time: Optional[str] = ""
    status: str = "PLANNED"
    notes: Optional[str] = ""


# ------------- Auth payloads -------------

class LoginIn(BaseModel):
    email: str
    password: str


class UserIn(BaseModel):
    name: str
    email: str
    password: Optional[str] = None
    role: str = "PENGAJAR"
    status: str = "ACTIVE"
    data_scope: str = "ALL"  # ALL or SCHOOL
    school_ids: List[str] = Field(default_factory=list)


class ForgotPasswordIn(BaseModel):
    email: str


class ResetPasswordIn(BaseModel):
    token: str
    password: str
