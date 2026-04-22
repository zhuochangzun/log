import httpx
from pydantic import BaseModel
from typing import Optional


class Warehouse(BaseModel):
    id: str
    name: str
    city: str


class Route(BaseModel):
    id: str
    from_city: str
    to_country: str
    to_city: str | None
    transit_days: int
    price_per_kg: float


class QuoteRequest(BaseModel):
    from_city: str
    to_country: str
    to_city: str | None = None
    weight: float


class QuoteResult(BaseModel):
    route_id: str
    warehouse_id: str
    total_price: float
    price_per_kg: float
    transit_days: int
    currency: str = "CNY"


class CreateOrderRequest(BaseModel):
    customer_id: str
    warehouse_id: str
    route_id: str
    weight: float
    from_address: str
    to_address: str
    to_contact: str
    to_phone: str


class OrderResult(BaseModel):
    dispatch_order_id: str
    status: str
    created_at: str


class DispatchAdapter:
    """调度系统 API 适配器"""

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.headers = {"Authorization": f"Bearer {api_key}"}

    async def list_warehouses(self) -> list[Warehouse]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/api/warehouses",
                headers=self.headers,
            )
            resp.raise_for_status()
            data = resp.json()
            return [Warehouse(**w) for w in data]

    async def get_routes(self, from_city: str, to_country: str) -> list[Route]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/api/routes",
                params={"from": from_city, "to": to_country},
                headers=self.headers,
            )
            resp.raise_for_status()
            data = resp.json()
            return [Route(**r) for r in data]

    async def calculate_quote(self, request: QuoteRequest) -> QuoteResult:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/api/quote",
                json=request.model_dump(),
                headers=self.headers,
            )
            resp.raise_for_status()
            return QuoteResult(**resp.json())

    async def create_order(self, request: CreateOrderRequest) -> OrderResult:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/api/orders",
                json=request.model_dump(),
                headers=self.headers,
            )
            resp.raise_for_status()
            return OrderResult(**resp.json())

    async def get_order(self, order_id: str) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/api/orders/{order_id}",
                headers=self.headers,
            )
            resp.raise_for_status()
            return resp.json()