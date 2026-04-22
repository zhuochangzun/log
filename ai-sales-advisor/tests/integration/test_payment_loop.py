import pytest
from unittest.mock import AsyncMock, MagicMock
from services.payment_loop import PaymentLoopService


@pytest.fixture
def mock_dispatch():
    dispatch = MagicMock()
    dispatch.create_order = AsyncMock(return_value=MagicMock(
        dispatch_order_id="ORD123",
        status="PENDING",
        created_at="2026-04-22T10:00:00Z",
    ))
    dispatch.get_order = AsyncMock(return_value={"bill_id": "BILL123"})
    dispatch.calculate_quote = AsyncMock(return_value=MagicMock(total_price=560.0))
    return dispatch


@pytest.fixture
def mock_cash():
    cash = MagicMock()
    cash.create_bill = AsyncMock(return_value=MagicMock(
        bill_id="BILL123",
        order_id="ORD123",
        amount=560.0,
        status="UNPAID",
        due_at="2026-04-25T10:00:00Z",
        created_at="2026-04-22T10:00:00Z",
    ))
    cash.check_payment_status = AsyncMock(return_value="PAID")
    cash.confirm_payment = AsyncMock()
    return cash


@pytest.mark.asyncio
async def test_create_order_and_bill(mock_dispatch, mock_cash):
    service = PaymentLoopService(mock_dispatch, mock_cash)

    order, bill = await service.create_order_and_bill(
        customer_id="CUST001",
        warehouse_id="WH_SH",
        route_id="ROUTE_US",
        weight=20.0,
        from_address="上海",
        to_address="纽约",
        to_contact="李经理",
        to_phone="13800001111",
    )

    assert order.id == "ORD123"
    assert order.total_amount == 560.0
    assert bill.id == "BILL123"
    assert bill.status == "UNPAID"


@pytest.mark.asyncio
async def test_verify_payment_before_ship_paid(mock_dispatch, mock_cash):
    service = PaymentLoopService(mock_dispatch, mock_cash)

    result = await service.verify_payment_before_ship("ORD123")

    assert result is True
    mock_cash.confirm_payment.assert_called_once_with("BILL123")


@pytest.mark.asyncio
async def test_verify_payment_before_ship_unpaid(mock_dispatch, mock_cash):
    mock_cash.check_payment_status = AsyncMock(return_value="UNPAID")
    service = PaymentLoopService(mock_dispatch, mock_cash)

    result = await service.verify_payment_before_ship("ORD123")

    assert result is False