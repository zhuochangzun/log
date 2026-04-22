from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class BillStatus(str, Enum):
    UNPAID = "UNPAID"             # 待付款
    PAID = "PAID"                  # 已付款
    REFUNDED = "REFUNDED"         # 已退款
    OVERDUE = "OVERDUE"            # 逾期


class Bill(BaseModel):
    id: str = Field(..., description="账单ID")
    order_id: str = Field(..., description="订单ID")
    amount: float = Field(..., description="账单金额")
    status: BillStatus = Field(BillStatus.UNPAID)
    due_at: datetime = Field(..., description="到期时间")
    paid_at: datetime | None = Field(None, description="付款时间")
    payment_channel: str | None = Field(None, description="支付渠道")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True