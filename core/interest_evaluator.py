"""
AstrBot Group Chat Plugin - Interest Evaluator
兴趣度评估器模块
"""

import re
import time
from typing import Dict, List, Any, Optional, Tuple, TYPE_CHECKING
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
        
        # 消息类型识别模式
        self.question_patterns = [
            r"^[？?]",  # 以问号开头
            r"[？?]$",  # 以问号结尾
            r"什么", r"怎么", r"为什么", r"哪里", r"谁", r"何时", r"多少",
            r"是否", r"能不能", r"会不会", r"有没有", r"可不可以",
            r"吗$", r"呢$", r"啊$", r"吧$"
        ]
        
        self.command_patterns = [
            r"^/",  # 斜杠命令
            r"^!",  # 感叹号命令
            r"请", r"帮忙", r"帮助", r"执行", r"运行", r"启动"
        ]
        
        self.greeting_patterns = [
            r"^(早上|中午|晚上)好", r"^(大家好|大家好啊)", r"^嗨", r"^hello", r"^hi",
            r"^(再见|拜拜|晚安)", r"^(回来了|在吗|在线吗)"
        ]
        
        self.emotion_patterns = [
            r"[哈哈呵呵嘻嘻]", r"[笑哭]", r"[泪]", r"[怒]", r"[赞]", r"[棒]",
            r"[😊-😭]", r"[🤣-🙄]", r"[😍-🥶]", r"[😎-🤩]", r"[🥳-🤯]"
        ]
        
        # 交互指示词
        self.interaction_words = {
            "@", "回复", "回答", "告诉", "解释", "说明", "介绍", "分析", "评价",
            "觉得", "认为", "看法", "意见", "建议", "推荐", "分享", "讨论"
        }
        
        logger.info("InterestEvaluator 初始化完成")
    
    async def evaluate_interest(self, event: AstrMessageEvent, user_state: UserState, 
                              group_state: GroupState) -> float:
        """评估消息兴趣度"""
        try:
            # 分析消息类型
            message_type = self._analyze_message_type(event.message_str)
            
            # 计算各项因素得分
            factors = InterestFactors()
            
            # 1. 消息类型得分
            factors.message_type_score = self._calculate_message_type_score(message_type)
            
            # 2. 内容长度得分
            factors.content_length_score = self._calculate_content_length_score(event.message_str)
            
            # 3. 交互性得分
            factors.interaction_score = self._calculate_interaction_score(event)
            
            # 4. 个人相关性得分
            factors.personal_relevance_score = self._calculate_personal_relevance_score(event, user_state)
            
            # 5. 上下文相关性得分
            factors.context_relevance_score = self._calculate_context_relevance_score(event, group_state)
            
            # 6. 时间因素得分
            factors.time_factor_score = self._calculate_time_factor_score(group_state)
            
            # 7. 发送者关系得分
            factors.sender_relationship_score = self._calculate_sender_relationship_score(user_state)
            
            # 综合计算最终兴趣度
            final_score = self._calculate_final_score(factors)
            
            if self.config.debug_mode:
                logger.debug(f"兴趣度评估结果: {final_score:.3f}")
                logger.debug(f"各因素得分: {factors}")
            
            return final_score
            
        except Exception as e:
            logger.error(f"评估兴趣度时发生错误: {e}")
            return 0.5  # 默认中等兴趣度
    
    def _analyze_message_type(self, message: str) -> MessageType:
        """分析消息类型"""
        message = message.strip()
        
        # 检查是否为命令
        for pattern in self.command_patterns:
            if re.search(pattern, message):
                return MessageType.COMMAND
        
        # 检查是否为问候
        for pattern in self.greeting_patterns:
            if re.search(pattern, message):
                return MessageType.GREETING
        
        # 检查是否为问题
        for pattern in self.question_patterns:
            if re.search(pattern, message):
                return MessageType.QUESTION
        
        # 检查是否包含情感表达
        for pattern in self.emotion_patterns:
            if re.search(pattern, message):
                return MessageType.EMOTION
        
        # 检查是否为回应（以"是的"、"不是"、"好的"等开头）
        response_starters = ["是的", "不是", "好的", "嗯", "对", "不对", "没错", "确实"]
        for starter in response_starters:
            if message.startswith(starter):
                return MessageType.RESPONSE
        
        # 默认为陈述
        return MessageType.STATEMENT
    
    def _calculate_message_type_score(self, message_type: MessageType) -> float:
        """计算消息类型得分"""
        type_scores = {
            MessageType.QUESTION: 0.8,      # 问题通常表示较高兴趣
            MessageType.COMMAND: 0.9,       # 命令表示明确需求
            MessageType.EMOTION: 0.6,       # 情感表达中等兴趣
            MessageType.GREETING: 0.4,      # 问候兴趣度较低
            MessageType.RESPONSE: 0.5,      # 回应中等兴趣
            MessageType.STATEMENT: 0.3,     # 陈述兴趣度一般
            MessageType.UNKNOWN: 0.2        # 未知类型兴趣度低
        }
        return type_scores.get(message_type, 0.3)
    
    def _calculate_content_length_score(self, message: str) -> float:
        """计算内容长度得分"""
        length = len(message.strip())
        
        if length == 0:
            return 0.0
        elif length <= 5:
            return 0.2  # 太短的内容兴趣度低
        elif length <= 15:
            return 0.4  # 短内容中等兴趣
        elif length <= 50:
            return 0.7  # 中等长度较高兴趣
        elif length <= 100:
            return 0.9  # 长内容高兴趣
        else:
            return 0.8  # 过长内容略降兴趣（可能是刷屏）
    
    def _calculate_interaction_score(self, event: AstrMessageEvent) -> float:
        """计算交互性得分"""
        message = event.message_str
        score = 0.0
        
        # 检查是否@了机器人
        if event.is_at_or_wake_command:
            score += 0.8
        
        # 检查是否包含交互指示词
        for word in self.interaction_words:
            if word in message:
                score += 0.3
        
        # 检查是否包含第二人称（"你"、"您"）
        if "你" in message or "您" in message:
            score += 0.2
        
        # 检查是否包含请求性词语
        request_words = ["请", "麻烦", "能否", "可以吗", "帮我"]
        for word in request_words:
            if word in message:
                score += 0.2
        
        return min(score, 1.0)
    
    def _calculate_personal_relevance_score(self, event: AstrMessageEvent, user_state: UserState) -> float:
        """计算个人相关性得分"""
        score = 0.0
        
        # 基于历史交互频率
        if user_state.reply_count > 0:
            interaction_frequency = user_state.conversation_streak / max(user_state.reply_count, 1)
            score += min(interaction_frequency * 0.3, 0.5)
        
        # 基于最近交互时间
        current_time = time.time()
        time_since_last_interaction = current_time - user_state.last_interaction_time
        
        if time_since_last_interaction < 300:  # 5分钟内交互过
            score += 0.3
        elif time_since_last_interaction < 3600:  # 1小时内交互过
            score += 0.2
        elif time_since_last_interaction < 86400:  # 24小时内交互过
            score += 0.1
        
        # 基于个人兴趣度
        score += user_state.personal_interest * 0.2
        
        return min(score, 1.0)
    
    def _calculate_context_relevance_score(self, event: AstrMessageEvent, group_state: GroupState) -> float:
        """计算上下文相关性得分"""
        score = 0.0
        
        # 基于群聊热度
        if group_state.chat_heat > 0.7:
            score += 0.3  # 热门群聊更值得关注
        elif group_state.chat_heat > 0.4:
            score += 0.2
        else:
            score += 0.1
        
        # 基于活跃用户数量
        active_user_count = len(group_state.active_users)
        if active_user_count > 10:
            score += 0.2  # 大群更活跃
        elif active_user_count > 5:
            score += 0.1
        
        # 基于消息频率
        current_time = time.time()
        time_since_last_message = current_time - group_state.last_message_time
        
        if time_since_last_message < 60:  # 1分钟内有消息
            score += 0.3  # 高频讨论
        elif time_since_last_message < 300:  # 5分钟内有消息
            score += 0.2
        else:
            score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_time_factor_score(self, group_state: GroupState) -> float:
        """计算时间因素得分"""
        current_time = time.time()
        hour = time.localtime(current_time).tm_hour
        
        # 根据时间段调整兴趣度
        if 9 <= hour <= 12:  # 上午
            return 0.7
        elif 14 <= hour <= 18:  # 下午
            return 0.8
        elif 19 <= hour <= 23:  # 晚上
            return 0.9
        elif 0 <= hour <= 6:  # 深夜
            return 0.4
        else:  # 凌晨
            return 0.5
    
    def _calculate_sender_relationship_score(self, user_state: UserState) -> float:
        """计算发送者关系得分"""
        score = 0.0
        
        # 基于连续对话计数
        if user_state.conversation_streak > 5:
            score += 0.4  # 长期对话伙伴
        elif user_state.conversation_streak > 2:
            score += 0.2
        elif user_state.conversation_streak > 0:
            score += 0.1
        
        # 基于疲劳程度（疲劳程度低表示关系好）
        score += (1.0 - user_state.fatigue_level) * 0.3
        
        # 基于个人兴趣度
        score += user_state.personal_interest * 0.3
        
        return min(score, 1.0)
    
    def _calculate_final_score(self, factors: InterestFactors) -> float:
        """计算最终兴趣度得分"""
        config = self.config
        
        # 使用配置中的权重
        weights = {
            'message_type': config.keyword_weight,
            'content_length': config.context_weight,
            'interaction': config.sender_weight,
            'personal_relevance': config.sender_weight,
            'context_relevance': config.context_weight,
            'time_factor': config.time_weight,
            'sender_relationship': config.sender_weight
        }
        
        # 计算加权得分
        weighted_score = (
            factors.message_type_score * weights['message_type'] +
            factors.content_length_score * weights['content_length'] +
            factors.interaction_score * weights['interaction'] +
            factors.personal_relevance_score * weights['personal_relevance'] +
            factors.context_relevance_score * weights['context_relevance'] +
            factors.time_factor_score * weights['time_factor'] +
            factors.sender_relationship_score * weights['sender_relationship']
        )
        
        # 归一化到0-1范围
        total_weight = sum(weights.values())
        normalized_score = weighted_score / total_weight if total_weight > 0 else 0.5
        
        # 应用阈值调整
        if normalized_score < config.interest_threshold:
            normalized_score *= 0.5  # 低于阈值的进一步降低
        
        return max(0.0, min(1.0, normalized_score))
    
    def get_interest_factors(self, event: AstrMessageEvent, user_state: UserState, 
                           group_state: GroupState) -> InterestFactors:
        """获取兴趣度因素详情（用于调试）"""
        # 分析消息类型
        message_type = self._analyze_message_type(event.message_str)
        
        # 计算各项因素得分
        factors = InterestFactors()
        factors.message_type_score = self._calculate_message_type_score(message_type)
        factors.content_length_score = self._calculate_content_length_score(event.message_str)
        factors.interaction_score = self._calculate_interaction_score(event)
        factors.personal_relevance_score = self._calculate_personal_relevance_score(event, user_state)
        factors.context_relevance_score = self._calculate_context_relevance_score(event, group_state)
        factors.time_factor_score = self._calculate_time_factor_score(group_state)
        factors.sender_relationship_score = self._calculate_sender_relationship_score(user_state)
        
        return factors
