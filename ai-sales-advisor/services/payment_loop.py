from datetime import datetime
from adapters import DispatchAdapter, CashAdapter
from adapters.dispatch_adapter import CreateOrderRequest
from models import Order, Bill, BillStatus


class PaymentLoopService:
    """收款闭环服务"""

    def __init__(
        self,
        dispatch_adapter: DispatchAdapter,
        cash_adapter: CashAdapter,
    ):
        self.dispatch = dispatch_adapter
        self.cash = cash_adapter

    async def create_order_and_bill(
        self,
        customer_id: str,
        warehouse_id: str,
        route_id: str,
        weight: float,
        from_address: str,
        to_address: str,
        to_contact: str,
        to_phone: str,
    ) -> tuple[Order, Bill]:
        """创建订单并生成账单"""

        # 1. 在调度系统创建订单
        order_result = await self.dispatch.create_order(
            request=CreateOrderRequest(
                customer_id=customer_id,
                warehouse_id=warehouse_id,
                route_id=route_id,
                weight=weight,
                from_address=from_address,
                to_address=to_address,
                to_contact=to_contact,
                to_phone=to_phone,
            )
        )

        # 2. 在出纳系统创建账单
        quote = await self.dispatch.calculate_quote(
            from_city=from_address,
            to_country=to_address,
            weight=weight,
        )
        bill_result = await self.cash.create_bill(
            order_id=order_result.dispatch_order_id,
            amount=quote.total_price,
            due_days=3,
        )

        order = Order(
            id=order_result.dispatch_order_id,
            dispatch_order_id=order_result.dispatch_order_id,
            customer_id=customer_id,
            warehouse_id=warehouse_id,
            route_id=route_id,
            status="PENDING",
            total_amount=quote.total_price,
            weight=weight,
            from_address=from_address,
            to_address=to_address,
            bill_id=bill_result.bill_id,
        )

        bill = Bill(
            id=bill_result.bill_id,
            order_id=order_result.dispatch_order_id,
            amount=quote.total_price,
            status=BillStatus.UNPAID,
            due_at=datetime.fromisoformat(bill_result.due_at),
        )

        return order, bill

    async def check_and_confirm_payment(self, bill_id: str) -> bool:
        """检查并确认付款状态"""
        status = await self.cash.check_payment_status(bill_id)
        if status == "PAID":
            await self.cash.confirm_payment(bill_id)
            return True
        return False

    async def verify_payment_before_ship(self, order_id: str) -> bool:
        """出库前校验付款状态"""
        order = await self.dispatch.get_order(order_id)
        bill_id = order.get("bill_id")
        if not bill_id:
            return False
        return await self.check_and_confirm_payment(bill_id)
