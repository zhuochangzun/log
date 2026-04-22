import json
import yaml
from pathlib import Path
from typing import Any
from .conversation_mgr import ConversationManager


class SkillEngine:
    """SKILL 执行引擎"""

    def __init__(self, skills_dir: Path, conversation_mgr: ConversationManager, handoff_service: Any | None = None):
        self.skills_dir = Path(skills_dir)
        self.conversation_mgr = conversation_mgr
        self.handoff_service = handoff_service
        self.skills: dict[str, dict] = {}
        self._load_skills()

    def _load_skills(self):
        """加载所有 SKILL 配置"""
        for skill_path in self.skills_dir.iterdir():
            if not skill_path.is_dir():
                continue
            skill_id = skill_path.name
            config_file = skill_path / "skill.json"
            if config_file.exists():
                with open(config_file) as f:
                    self.skills[skill_id] = json.load(f)

    def match_skill(self, message: str) -> str | None:
        """根据消息内容匹配 SKILL"""
        message_lower = message.lower()
        for skill_id, skill in self.skills.items():
            keywords = skill.get("trigger_keywords", [])
            for kw in keywords:
                if kw.lower() in message_lower:
                    return skill_id
        return "SKL101"  # 默认使用接待 SKILL

    async def execute_skill(
        self,
        skill_id: str,
        message: str,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """执行指定 SKILL"""
        skill_path = self.skills_dir / skill_id
        prompt_file = skill_path / "prompt.md"

        # 加载 prompt
        if prompt_file.exists():
            with open(prompt_file) as f:
                prompt_template = f.read()
        else:
            prompt_template = f"# {skill_id}\n\n处理消息: {message}"

        # TODO: 调用 LLM 生成回复
        # 目前返回占位符
        response = f"[{skill_id}] 处理中: {message}"

        return {
            "skill_id": skill_id,
            "response": response,
            "context": context,
        }

    async def process_message(
        self,
        conversation_id: str,
        message: str,
    ) -> dict[str, Any]:
        """处理用户消息"""
        conversation = await self.conversation_mgr.get_conversation(conversation_id)
        context = conversation.get("context", {}) if conversation else {}

        # 检查是否需要转人工
        if self.handoff_service:
            should_handoff, reason = self.handoff_service.should_handoff(message)
            if should_handoff:
                handoff_result = await self.handoff_service.execute_handoff(conversation, reason)
                return {
                    "type": "handoff",
                    "handoff": handoff_result,
                }

        skill_id = self.match_skill(message)

        result = await self.execute_skill(skill_id, message, context)

        # 保存消息到会话
        await self.conversation_mgr.add_message(
            conversation_id=conversation_id,
            sender="AI",
            content=result["response"],
            skill_triggered=skill_id,
        )

        return result
