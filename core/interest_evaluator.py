"""
AstrBot Group Chat Plugin - Interest Evaluator
兴趣度评估器模块
"""

import re
import time
from typing import TYPE_CHECKING
from dataclasses import dataclass
from enum import Enum

from astrbot.api.event import AstrMessageEvent
from astrbot.api import logger

from .chat_manager import UserState, GroupState

if TYPE_CHECKING:
    from ..config.plugin_config import PluginConfig


class MessageType(Enum):
    """消息类型分析"""
    QUESTION = "question"  # 问题
    STATEMENT = "statement"  # 陈述
    EMOTION = "emotion"  # 情感表达
    COMMAND = "command"  # 命令
    GREETING = "greeting"  # 问候
    RESPONSE = "response"  # 回应
    UNKNOWN = "unknown"  # 未知


@dataclass
class InterestFactors:
    """兴趣度因素"""
    message_type_score: float = 0.0  # 消息类型得分
    content_length_score: float = 0.0  # 内容长度得分
    interaction_score: float = 0.0  # 交互性得分
    personal_relevance_score: float = 0.0  # 个人相关性得分
    context_relevance_score: float = 0.0  # 上下文相关性得分
    time_factor_score: float = 0.0  # 时间因素得分
    sender_relationship_score: float = 0.0  # 发送者关系得分


class InterestEvaluator:
    """兴趣度评估器"""

    def __init__(self, plugin_config: "PluginConfig"):
        self.config: "PluginConfig" = plugin_config
        logger.info("InterestEvaluator 初始化完成")

    async def evaluate_interest(self, event: AstrMessageEvent, user_state: UserState,
                              group_state: GroupState) -> float:
        """评估消息兴趣度"""
        try:
            message_type = self._analyze_message_type(event.message_str)
            factors = self.get_interest_factors(event, user_state, group_state)
            final_score = self._calculate_final_score(factors)

            if self.config.debug_mode:
                logger.debug(f"兴趣度评估结果: {final_score:.3f}")
                logger.debug(f"各因素得分: {factors}")

            return final_score
        except Exception as e:
            logger.error(f"评估兴趣度时发生错误: {e}")
            return 0.5

    def _analyze_message_type(self, message: str) -> MessageType:
        """分析消息类型"""
        message = message.strip()
        if not message:
            return MessageType.UNKNOWN

        if message.startswith('/') or message.startswith('!'):
            return MessageType.COMMAND
        if message.endswith(('?', '？')):
            return MessageType.QUESTION
        if re.search(r"[\U0001F600-\U0001F64F]", message):  # 简单的Emoji检测
            return MessageType.EMOTION
        if len(message) <= 10:  # 短消息可能是问候或简单回应
            return MessageType.GREETING
        
        return MessageType.STATEMENT

    def _calculate_message_type_score(self, message_type: MessageType) -> float:
        """计算消息类型得分"""
        type_scores = {
            MessageType.QUESTION: 0.9,
            MessageType.COMMAND: 0.9,
            MessageType.EMOTION: 0.5,
            MessageType.GREETING: 0.2,
            MessageType.RESPONSE: 0.6,
            MessageType.STATEMENT: 0.4,
            MessageType.UNKNOWN: 0.1
        }
        return type_scores.get(message_type, 0.4)

    def _calculate_content_length_score(self, message: str) -> float:
        """计算内容长度得分"""
        length = len(message.strip())
        if length == 0: return 0.0
        if length <= 10: return 0.2
        if length <= 40: return 0.6
        if length <= 100: return 0.9
        return 0.7

    def _calculate_interaction_score(self, event: AstrMessageEvent, group_state: GroupState) -> float:
        """计算交互性得分"""
        score = 0.0
        if event.is_at_or_wake_command:
            score += 0.8
        
        time_since_last = time.time() - group_state.last_message_time
        if time_since_last < 60:
            score += 0.3
            
        return min(score, 1.0)

    def _calculate_personal_relevance_score(self, user_state: UserState) -> float:
        """计算个人相关性得分"""
        score = 0.0
        if user_state.reply_count > 0:
            freq = user_state.conversation_streak / user_state.reply_count
            score += min(freq * 0.4, 0.6)

        time_since_last = time.time() - user_state.last_interaction_time
        if time_since_last < 300: score += 0.4
        elif time_since_last < 3600: score += 0.2
            
        return min(score, 1.0)

    def _calculate_context_relevance_score(self, group_state: GroupState) -> float:
        """计算上下文相关性得分"""
        score = group_state.chat_heat * 0.5
        
        active_users = len(group_state.active_users)
        if active_users > 10: score += 0.3
        elif active_users > 5: score += 0.15

        time_since_last = time.time() - group_state.last_message_time
        if time_since_last < 60: score += 0.2
        elif time_since_last < 300: score += 0.1

        return min(score, 1.0)

    def _calculate_time_factor_score(self) -> float:
        """计算时间因素得分"""
        hour = time.localtime(time.time()).tm_hour
        if 14 <= hour <= 17 or 20 <= hour <= 23: return 0.9
        if 9 <= hour <= 12: return 0.7
        if 0 <= hour <= 6: return 0.3
        return 0.5

    def _calculate_sender_relationship_score(self, user_state: UserState) -> float:
        """计算发送者关系得分"""
        score = min(user_state.conversation_streak * 0.1, 0.5)
        score += (1.0 - user_state.fatigue_level) * 0.5
        return min(score, 1.0)

    def _calculate_final_score(self, factors: InterestFactors) -> float:
        """计算最终兴趣度得分"""
        # 复用现有配置权重，但赋予新的逻辑含义
        weights = {
            'message_type': self.config.keyword_weight,       # 原 keyword_weight -> message_type
            'content_length': self.config.context_weight,     # 原 context_weight -> content_length
            'interaction': self.config.sender_weight,         # 原 sender_weight -> interaction
            'personal_relevance': self.config.sender_weight,  # 复用 sender_weight
            'context_relevance': self.config.context_weight,  # 复用 context_weight
            'time_factor': self.config.time_weight,
            'sender_relationship': self.config.sender_weight  # 复用 sender_weight
        }
        
        weighted_score = (
            factors.message_type_score * weights['message_type'] +
            factors.content_length_score * weights['content_length'] +
            factors.interaction_score * weights['interaction'] +
            factors.personal_relevance_score * weights['personal_relevance'] +
            factors.context_relevance_score * weights['context_relevance'] +
            factors.time_factor_score * weights['time_factor'] +
            factors.sender_relationship_score * weights['sender_relationship']
        )
        
        total_weight = sum(weights.values())
        if total_weight == 0: return 0.5
            
        normalized_score = weighted_score / total_weight
        
        if normalized_score < self.config.interest_threshold:
            normalized_score *= 0.7

        return max(0.0, min(1.0, normalized_score))

    def get_interest_factors(self, event: AstrMessageEvent, user_state: UserState,
                           group_state: GroupState) -> InterestFactors:
        """获取兴趣度因素详情"""
        message_type = self._analyze_message_type(event.message_str)
        factors = InterestFactors()
        factors.message_type_score = self._calculate_message_type_score(message_type)
        factors.content_length_score = self._calculate_content_length_score(event.message_str)
        factors.interaction_score = self._calculate_interaction_score(event, group_state)
        factors.personal_relevance_score = self._calculate_personal_relevance_score(user_state)
        factors.context_relevance_score = self._calculate_context_relevance_score(group_state)
        factors.time_factor_score = self._calculate_time_factor_score()
        factors.sender_relationship_score = self._calculate_sender_relationship_score(user_state)
        return factors
