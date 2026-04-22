import pytest
from adapters.wechat_adapter import WeChatAdapter


@pytest.fixture
def wechat_adapter():
    return WeChatAdapter(
        corp_id="test_corp_id",
        agent_id="test_agent_id",
        secret="test_secret",
    )


@pytest.mark.asyncio
async def test_send_text_message(wechat_adapter, respx_mock):
    """发送文本消息"""
    respx_mock.get("https://qyapi.weixin.qq.com/cgi-bin/gettoken").mock(
        return_value=Response(200, json={"access_token": "test_token"})
    )
    respx_mock.post("https://qyapi.weixin.qq.com/cgi-bin/message/send").mock(
        return_value=Response(200, json={"errcode": 0, "errmsg": "ok"})
    )

    result = await wechat_adapter.send_text("user123", "您好，有什么可以帮您？")

    assert result["errcode"] == 0


@pytest.mark.asyncio
async def test_get_user_info(wechat_adapter, respx_mock):
    """获取用户信息"""
    respx_mock.get("https://qyapi.weixin.qq.com/cgi-bin/gettoken").mock(
        return_value=Response(200, json={"access_token": "test_token"})
    )
    respx_mock.get("https://qyapi.weixin.qq.com/cgi-bin/user/get").mock(
        return_value=Response(200, json={
            "errcode": 0,
            "errmsg": "ok",
            "userid": "user123",
            "name": "张三",
        })
    )

    result = await wechat_adapter.get_user_info("user123")

    assert result["name"] == "张三"
