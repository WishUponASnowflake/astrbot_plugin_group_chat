import time
from typing import TYPE_CHECKING, Any, Dict

from astrbot.api import logger

if TYPE_CHECKING:
    from state_manager import StateManager

class FocusChatManager:
    """专注聊天管理器"""

    def __init__(self, context: Any, config: Any, state_manager: "StateManager"):
        self.context = context
        self.config = config
        self.state_manager = state_manager

    async def evaluate_focus_interest(self, event: Any, chat_context: Dict) -> float:
        """评估专注聊天兴趣度"""
        user_id = event.get_sender_id()
        message_content = event.message_str

        # 计算兴趣度分数
        interest_score = 0.0

        # 1. 检查是否@机器人
        if event.is_at_or_wake_command:
            interest_score += 0.4

        # 2. 检查消息相关性
        if self._is_message_relevant(message_content, chat_context):
            interest_score += 0.3

        # 3. 检查用户印象
        user_impression = self.state_manager.get_user_impression(user_id)
        impression_score = user_impression.get("score", 0.5)
        interest_score += impression_score * 0.3

        return min(1.0, interest_score)
    
    def _is_message_relevant(self, message_content: str, chat_context: Dict) -> bool:
        """检查消息相关性"""
        # 简单的相关性检查
        relevant_keywords = ["机器人", "助手", "帮忙", "请问", "谢谢", "你好"]
        
        # 检查是否包含相关关键词
        for keyword in relevant_keywords:
            if keyword in message_content:
                return True
        
        # 检查是否是问句
        question_markers = ["？", "?", "吗", "呢", "啊"]
        for marker in question_markers:
            if marker in message_content:
                return True
        
        return False
    
    async def enter_focus_mode(self, group_id: str, target_user_id: str):
        """进入专注聊天模式"""
        if not getattr(self.config, 'focus_chat_enabled', True):
            return

        self.state_manager.set_interaction_mode(group_id, "focus")
        self.state_manager.set_focus_target(group_id, target_user_id)

        logger.info(f"群组 {group_id} 进入专注聊天模式，目标用户：{target_user_id}")

    async def should_exit_focus_mode(self, group_id: str, target_user_id: str) -> bool:
        """检查是否应该退出专注模式"""
        current_target = self.state_manager.get_focus_target(group_id)
        if current_target != target_user_id:
            return True

        # 检查超时
        last_activity = self.state_manager.get_last_activity(target_user_id)
        timeout = getattr(self.config, 'focus_timeout_seconds', 300)
        if time.time() - last_activity > timeout:
            return True

        # 检查回复次数限制
        response_count = self.state_manager.get_focus_response_count(group_id)
        max_responses = getattr(self.config, 'focus_max_responses', 10)
        if response_count >= max_responses:
            return True

        return False

    async def exit_focus_mode(self, group_id: str):
        """退出专注聊天模式"""
        self.state_manager.set_interaction_mode(group_id, "normal")
        self.state_manager.clear_focus_target(group_id)
        self.state_manager.clear_focus_response_count(group_id)

        logger.info(f"群组 {group_id} 退出专注聊天模式")

    def increment_focus_response_count(self, group_id: str):
        """增加专注聊天回复计数"""
        self.state_manager.increment_focus_response_count(group_id)
