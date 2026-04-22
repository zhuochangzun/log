from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class OrderStatus(str, Enum):
    PENDING = "PENDING"           # 待付款
    PAID = "PAID"                 # 已付款
    SHIPPED = "SHIPPED"           # 已发货
    DELIVERED = "DELIVERED"       # 已签收
    CANCELLED = "CANCELLED"       # 已取消


class Order(BaseModel):
    id: str = Field(..., description="订单ID")
    dispatch_order_id: str = Field(..., description="调度系统订单ID")
    customer_id: str = Field(..., description="客户ID")
    warehouse_id: str = Field(..., description="仓库ID")
    route_id: str = Field(..., description="路线ID")
    status: OrderStatus = Field(OrderStatus.PENDING)
    total_amount: float = Field(..., description="总金额")
    weight: float = Field(..., description="重量kg")
    from_address: str = Field(..., description="发货地址")
    to_address: str = Field(..., description="收货地址")
    bill_id: str | None = Field(None, description="账单ID")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True