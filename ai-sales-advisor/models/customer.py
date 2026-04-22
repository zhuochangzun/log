from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class CustomerTier(str, Enum):
    VIP = "VIP"
    NORMAL = "NORMAL"
    POTENTIAL = "POTENTIAL"


class Customer(BaseModel):
    id: str = Field(..., description="客户ID")
    name: str = Field(..., description="姓名")
    phone: str = Field(..., description="手机号")
    company: str | None = Field(None, description="公司名称")
    wechat_openid: str | None = Field(None, description="微信OpenID")
    tier: CustomerTier = Field(CustomerTier.NORMAL)
    crm_id: str | None = Field(None, description="CRM系统ID")
    visitor_id: str = Field(..., description="访客ID")
    source: str = Field(..., description="来源渠道: wechat/website/phone")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True