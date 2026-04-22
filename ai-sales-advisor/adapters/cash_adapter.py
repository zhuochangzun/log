import httpx
from pydantic import BaseModel
from datetime import datetime


class CreateBillRequest(BaseModel):
    order_id: str
    amount: float
    due_days: int = 3


class BillResult(BaseModel):
    bill_id: str
    order_id: str
    amount: float
    status: str
    due_at: str
    created_at: str


class CashAdapter:
    """出纳系统 API 适配器"""

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.headers = {"Authorization": f"Bearer {api_key}"}

    async def create_bill(self, request: CreateBillRequest) -> BillResult:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/api/bills",
                json=request.model_dump(),
                headers=self.headers,
            )
            resp.raise_for_status()
            return BillResult(**resp.json())

    async def get_bill(self, bill_id: str) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/api/bills/{bill_id}",
                headers=self.headers,
            )
            resp.raise_for_status()
            return resp.json()

    async def confirm_payment(self, bill_id: str, payment_info: dict | None = None) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/api/bills/{bill_id}/paid",
                json=payment_info or {},
                headers=self.headers,
            )
            resp.raise_for_status()
            return resp.json()

    async def check_payment_status(self, bill_id: str) -> str:
        bill = await self.get_bill(bill_id)
        return bill.get("status", "UNKNOWN")