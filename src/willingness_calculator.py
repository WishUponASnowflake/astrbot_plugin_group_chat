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
        """计算多维度群活跃度"""
        conversation_history = chat_context.get("conversation_history", [])
        if not conversation_history:
            return 0.0

        current_time = time.time()

        # 1. 时间窗口分析（多时间段）
        time_windows = [
            (60, 0.4),   # 最近1分钟，权重40%
            (300, 0.3),  # 最近5分钟，权重30%
            (1800, 0.2), # 最近30分钟，权重20%
            (3600, 0.1), # 最近1小时，权重10%
        ]

        activity_score = 0.0
        for window_seconds, weight in time_windows:
            recent_count = sum(1 for msg in conversation_history
                             if current_time - msg.get("timestamp", 0) < window_seconds)
            # 标准化到0-1范围（假设每分钟最大5条消息为活跃）
            normalized_count = min(1.0, recent_count / (window_seconds / 60 * 5))
            activity_score += normalized_count * weight

        # 2. 用户参与度分析
        recent_users = set()
        for msg in conversation_history:
            if current_time - msg.get("timestamp", 0) < 300:  # 最近5分钟
                recent_users.add(msg.get("user_id", ""))

        user_participation = min(1.0, len(recent_users) / 10.0)  # 假设10个活跃用户为满分

        # 3. 消息质量评估
        quality_score = self._assess_message_quality(conversation_history, current_time)

        # 4. 话题持续性分析
        topic_continuity = self._assess_topic_continuity(conversation_history, current_time)

        # 综合评分（活跃度40% + 用户参与30% + 质量20% + 持续性10%）
        final_activity = (
            activity_score * 0.4 +
            user_participation * 0.3 +
            quality_score * 0.2 +
            topic_continuity * 0.1
        )

        return min(1.0, max(0.0, final_activity))

    def _assess_message_quality(self, conversation_history: list, current_time: float) -> float:
        """评估消息质量"""
        recent_messages = [msg for msg in conversation_history
                          if current_time - msg.get("timestamp", 0) < 300]

        if not recent_messages:
            return 0.0

        quality_scores = []
        for msg in recent_messages:
            content = msg.get("content", "")
            score = 0.0

            # 长度评估（太短或太长都降低质量）
            content_length = len(content.strip())
            if 5 <= content_length <= 200:
                score += 0.3
            elif content_length > 200:
                score += 0.1  # 过长消息质量较低

            # 互动性评估（包含@、问号等）
            if "@" in content or "？" in content or "?" in content:
                score += 0.4

            # 情感表达评估（包含表情符号、感叹号等）
            if any(char in content for char in ["！", "!", "😊", "😂", "👍", "❤️"]):
                score += 0.3

            quality_scores.append(min(1.0, score))

        return sum(quality_scores) / len(quality_scores) if quality_scores else 0.0

    def _assess_topic_continuity(self, conversation_history: list, current_time: float) -> float:
        """评估话题持续性"""
        recent_messages = [msg for msg in conversation_history
                          if current_time - msg.get("timestamp", 0) < 600]  # 最近10分钟

        if len(recent_messages) < 3:
            return 0.0

        # 简单的话题持续性：检查是否有重复的用户交互
        user_sequence = [msg.get("user_id", "") for msg in recent_messages[-10:]]
        continuity_score = 0.0

        # 检查连续对话模式
        for i in range(len(user_sequence) - 1):
            if user_sequence[i] == user_sequence[i + 1]:
                continuity_score += 0.2  # 连续发言加分

        # 检查回复模式（用户A -> 用户B -> 用户A）
        if len(user_sequence) >= 3:
            for i in range(len(user_sequence) - 2):
                if (user_sequence[i] == user_sequence[i + 2] and
                    user_sequence[i] != user_sequence[i + 1]):
                    continuity_score += 0.3  # 回复模式加分

        return min(1.0, continuity_score)
    
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
