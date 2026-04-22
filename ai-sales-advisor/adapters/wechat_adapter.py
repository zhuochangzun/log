import httpx
from pydantic import BaseModel
from typing import Optional


class WeChatMessage(BaseModel):
    """企业微信消息"""
    to_user: str
    msg_type: str = "text"
    content: str


class WeChatTextMessage(WeChatMessage):
    msg_type: str = "text"


class WeChatImageMessage(WeChatMessage):
    msg_type: str = "image"
    media_id: str


class WeChatCardMessage(WeChatMessage):
    msg_type: str = "miniprogram_card"
    title: str
    description: str
    url: str
    picurl: str


class WeChatAdapter:
    """企业微信 SDK 适配器"""

    def __init__(self, corp_id: str, agent_id: str, secret: str):
        self.corp_id = corp_id
        self.agent_id = agent_id
        self.secret = secret
        self._access_token: str | None = None

    async def _get_access_token(self) -> str:
        """获取 access_token"""
        if self._access_token:
            return self._access_token

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://qyapi.weixin.qq.com/cgi-bin/gettoken",
                params={
                    "corpid": self.corp_id,
                    "corpsecret": self.secret,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            self._access_token = data["access_token"]
            return self._access_token

    async def send_text(self, to_user: str, content: str) -> dict:
        """发送文本消息"""
        token = await self._get_access_token()
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://qyapi.weixin.qq.com/cgi-bin/message/send",
                params={"access_token": token},
                json={
                    "touser": to_user,
                    "msgtype": "text",
                    "agentid": self.agent_id,
                    "text": {"content": content},
                },
            )
            resp.raise_for_status()
            return resp.json()

    async def send_image(self, to_user: str, media_id: str) -> dict:
        """发送图片消息"""
        token = await self._get_access_token()
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://qyapi.weixin.qq.com/cgi-bin/message/send",
                params={"access_token": token},
                json={
                    "touser": to_user,
                    "msgtype": "image",
                    "agentid": self.agent_id,
                    "image": {"media_id": media_id},
                },
            )
            resp.raise_for_status()
            return resp.json()

    async def send_bill_card(self, to_user: str, bill_info: dict) -> dict:
        """发送账单卡片消息"""
        token = await self._get_access_token()
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://qyapi.weixin.qq.com/cgi-bin/message/send",
                params={"access_token": token},
                json={
                    "touser": to_user,
                    "msgtype": "miniprogram_card",
                    "agentid": self.agent_id,
                    "miniprogram_card": {
                        "title": f"账单 #{bill_info['bill_id']}",
                        "description": f"应付金额：{bill_info['amount']}",
                        "url": bill_info.get("payment_url", ""),
                        "picurl": bill_info.get("qr_code_url", ""),
                    },
                },
            )
            resp.raise_for_status()
            return resp.json()

    async def get_user_info(self, user_id: str) -> dict:
        """获取企业微信用户信息"""
        token = await self._get_access_token()
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://qyapi.weixin.qq.com/cgi-bin/user/get",
                params={"access_token": token, "userid": user_id},
            )
            resp.raise_for_status()
            return resp.json()

    async def create_menu(self, menu_config: dict) -> dict:
        """创建应用菜单"""
        token = await self._get_access_token()
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://qyapi.weixin.qq.com/cgi-bin/menu/create",
                params={"access_token": token, "agentid": self.agent_id},
                json=menu_config,
            )
            resp.raise_for_status()
            return resp.json()