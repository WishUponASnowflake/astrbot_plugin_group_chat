import json
from typing import TYPE_CHECKING, Any, Dict

from astrbot.api.star import Context

if TYPE_CHECKING:
    from state_manager import StateManager
    from impression_manager import ImpressionManager
    from memory_integration import MemoryIntegration

class ContextAnalyzer:
    """上下文分析器"""

    def __init__(self, context: Context, config: Any,
                 state_manager: "StateManager",
                 impression_manager: "ImpressionManager",
                 memory_integration: "MemoryIntegration"):
        self.context = context
        self.config = config
        self.state_manager = state_manager
        self.impression_manager = impression_manager
        self.memory_integration = memory_integration

    async def analyze_chat_context(self, event: Any) -> Dict:
        """分析聊天上下文"""
        group_id = event.get_group_id()
        user_id = event.get_sender_id()

        # 获取对话历史
        curr_cid = await self.context.conversation_manager.get_curr_conversation_id(event.unified_msg_origin)
        conversation_history = []
        if curr_cid:
            conversation = await self.context.conversation_manager.get_conversation(event.unified_msg_origin, curr_cid)
            if conversation:
                conversation_history = json.loads(conversation.history)

        # 获取用户印象
        user_impression = await self.impression_manager.get_user_impression(user_id, group_id)

        # 获取相关记忆（不使用关键词，基于内容语义）
        relevant_memories = await self.memory_integration.recall_memories(
            message_content=event.message_str,
            group_id=group_id
        )

        conversation_counts = self.state_manager.get_conversation_counts()
        group_counts = conversation_counts.get(group_id, {})

        return {
            "group_id": group_id,
            "user_id": user_id,
            "conversation_history": conversation_history,
            "user_impression": user_impression,
            "relevant_memories": relevant_memories,
            "current_mode": self.state_manager.get_interaction_modes().get(group_id, "normal"),
            "focus_target": self.state_manager.get_focus_targets().get(group_id),
            "fatigue_count": self.state_manager.get_fatigue_data().get(user_id, 0),
            "conversation_count": group_counts.get(user_id, 0)
        }
