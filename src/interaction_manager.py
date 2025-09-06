import time
from typing import Any, Dict

from astrbot.api import logger
from astrbot.api.star import Context
from state_manager import StateManager

class InteractionManager:
    """交互管理器"""
    
    def __init__(self, context: Context, config: Any, state_manager: StateManager):
        self.context = context
        self.config = config
        self.state_manager = state_manager
    
    def determine_interaction_mode(self, chat_context: Dict) -> str:
        """判断交互模式"""
        group_activity = self._calculate_group_activity(chat_context)
        observation_threshold = getattr(self.config, 'observation_mode_threshold', 0.2)
        
        if group_activity < observation_threshold:
            return "observation"  # 观察模式
        
        # 检查是否在专注聊天中
        current_mode = chat_context.get("current_mode", "normal")
        if current_mode == "focus":
            return "focus"
        
        return "normal"
    
    def _calculate_group_activity(self, chat_context: Dict) -> float:
        """计算群活跃度"""
        conversation_history = chat_context.get("conversation_history", [])
        if not conversation_history:
            return 0.0
        
        # 简单的活跃度计算：最近5分钟内的消息数量
        current_time = time.time()
        recent_count = sum(1 for msg in conversation_history if current_time - msg.get("timestamp", 0) < 300)
        
        return min(1.0, recent_count / 10.0)  # 假设10条消息为最大活跃度
    
    async def update_interaction_state(self, event: Any, chat_context: Dict, response_result: Dict):
        """更新交互状态"""
        group_id = event.get_group_id()
        user_id = event.get_sender_id()
        current_time = time.time()
        
        # 更新最后活动时间
        self.state_manager.update_last_activity(group_id, current_time)
        self.state_manager.update_last_activity(user_id, current_time)
        
        # 更新对话计数
        self.state_manager.increment_conversation_count(group_id, user_id)
        
        # 如果未回复，重置连续回复计数器
        if not response_result.get("should_reply"):
            self.state_manager.reset_consecutive_response(group_id)
        
        # 检查专注模式退出条件
        if chat_context.get("current_mode") == "focus":
            await self._check_focus_mode_exit(group_id, user_id, current_time, response_result)
        
        # 记录读空气决策统计
        if response_result.get("decision_method") == "air_reading":
            await self._update_air_reading_stats(group_id, response_result)
    
    async def _check_focus_mode_exit(self, group_id: str, user_id: str, current_time: float, response_result: Dict):
        """检查是否需要退出专注模式"""
        focus_targets = self.state_manager.get_focus_targets()
        focus_target = focus_targets.get(group_id)

        if focus_target and focus_target != user_id:
            last_target_activity = self.state_manager.get_last_activity(focus_target)
            focus_timeout = getattr(self.config, 'focus_timeout_seconds', 300)

            if current_time - last_target_activity > focus_timeout:
                self.state_manager.set_interaction_mode(group_id, "normal")
                self.state_manager.remove_focus_target(group_id)
                logger.info(f"群组 {group_id} 因超时退出专注聊天模式")
    
    async def _update_air_reading_stats(self, group_id: str, response_result: Dict):
        """更新读空气统计信息"""
        # 这里可以添加读空气决策的统计逻辑
        # 比如记录 LLM 跳过回复的频率，用于优化系统
        pass
