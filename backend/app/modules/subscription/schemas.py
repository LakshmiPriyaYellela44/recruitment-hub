from pydantic import BaseModel
from datetime import datetime
from typing import List


class UpgradeSubscriptionRequest(BaseModel):
    subscription_type: str  # PRO
    payment_method: str = "credit_card"


class SubscriptionResponse(BaseModel):
    user_id: str
    subscription_type: str
    message: str


class SetRecruiterSubscriptionRequest(BaseModel):
    subscription_type: str  # BASIC or PRO


class RecruiterSubscriptionResponse(BaseModel):
    recruiter_id: str
    subscription_type: str
    message: str


class RecruiterInfo(BaseModel):
    id: str
    email: str
    first_name: str | None
    last_name: str | None
    subscription_type: str
    is_active: bool
    created_at: datetime


class AdminListRecruitersResponse(BaseModel):
    recruiters: List[RecruiterInfo]
    total: int
    limit: int
    offset: int
