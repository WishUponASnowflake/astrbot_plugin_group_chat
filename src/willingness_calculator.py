import time
from typing import Any, Dict

from astrbot.api import logger
from astrbot.api.star import Context
from state_manager import StateManager
from impression_manager import ImpressionManager

class WillingnessCalculator:
    """意愿计算器"""
    
    def __init__(self, context: Context, config: Any, impression_manager: ImpressionManager, state_manager: StateManager):
        self.context = context
        self.config = config
        self.impression_manager = impression_manager
        self.state_manager = state_manager
    
    async def calculate_response_willingness(self, event: Any, chat_context: Dict) -> Dict:
        """计算回复意愿，返回包含决策结果的字典"""
        user_id = event.get_sender_id()
        group_id = event.get_group_id()
        
        # 获取配置
        base_probability = getattr(self.config, 'base_probability', 0.3)
        willingness_threshold = getattr(self.config, 'willingness_threshold', 0.5)
        
        # 获取用户印象
        user_impression = await self.impression_manager.get_user_impression(user_id, group_id)
        impression_score = user_impression.get("score", 0.5)
        
        # 计算各种因素
        group_activity = self._calculate_group_activity(chat_context)
        continuity_bonus = self._calculate_continuity_bonus(user_id, chat_context)
        fatigue_penalty = self._calculate_fatigue_penalty(user_id, chat_context)
        
        # 综合计算基础意愿值
        calculated_willingness = (
            base_probability * 0.3 +
            impression_score * 0.4 +
            group_activity * 0.2 +
            continuity_bonus * 0.1 -
            fatigue_penalty
        )
        
        final_willingness = max(0.0, min(1.0, calculated_willingness))
        
        # 如果启用读空气功能，让 LLM 做最终决策
        if getattr(self.config, 'air_reading_enabled', True):
            return {
                "should_respond": None,  # 由 LLM 决定
                "willingness_score": final_willingness,
                "requires_llm_decision": True,
                "decision_context": {
                    "base_willingness": final_willingness,
                    "impression_score": impression_score,
                    "group_activity": group_activity,
                    "fatigue_level": fatigue_penalty,
                    "interaction_mode": chat_context.get("current_mode", "normal")
                }
            }
        else:
            return {
                "should_respond": final_willingness >= willingness_threshold,
                "willingness_score": final_willingness,
                "requires_llm_decision": False,
                "decision_context": {
                    "base_willingness": final_willingness,
                    "threshold": willingness_threshold
                }
            }
    
    def _calculate_group_activity(self, chat_context: Dict) -> float:
        """计算群活跃度"""
        conversation_history = chat_context.get("conversation_history", [])
        if not conversation_history:
            return 0.0
        
        # 简单的活跃度计算：最近5分钟内的消息数量
        current_time = time.time()
        recent_count = sum(1 for msg in conversation_history if current_time - msg.get("timestamp", 0) < 300)
        
        return min(1.0, recent_count / 10.0)  # 假设10条消息为最大活跃度
    
    def _calculate_continuity_bonus(self, user_id: str, chat_context: Dict) -> float:
        """计算连续对话奖励"""
        conversation_history = chat_context.get("conversation_history", [])
        
        # 检查是否与同一用户连续对话
        if len(conversation_history) >= 2:
            last_two = conversation_history[-2:]
            if all(msg.get("user_id") == user_id for msg in last_two):
                return 0.3  # 连续对话奖励
        
        return 0.0
    
    def _calculate_fatigue_penalty(self, user_id: str, chat_context: Dict) -> float:
        """计算疲劳度惩罚"""
        fatigue_data = self.state_manager.get_fatigue_data()
        user_fatigue = fatigue_data.get(user_id, 0)
        
        # 根据疲劳度计算惩罚
        fatigue_threshold = getattr(self.config, 'fatigue_threshold', 5)
        if user_fatigue >= fatigue_threshold:
            return 0.5  # 高疲劳度惩罚
        
        return user_fatigue * 0.05  # 线性疲劳惩罚
