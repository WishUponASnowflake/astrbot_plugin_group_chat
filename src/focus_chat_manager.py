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
        """智能相关性检测（不使用关键词）"""
        # 1. 结构化特征分析
        structural_score = self._analyze_structural_features(message_content)

        # 2. 上下文一致性分析
        context_score = self._analyze_context_consistency(message_content, chat_context)

        # 3. 用户行为模式分析
        behavior_score = self._analyze_user_behavior_pattern(chat_context)

        # 4. 对话流分析
        flow_score = self._analyze_conversation_flow(chat_context)

        # 5. 时间相关性分析
        time_score = self._analyze_temporal_relevance(chat_context)

        # 综合评分（各维度权重可调整）
        total_score = (
            structural_score * 0.25 +  # 结构特征25%
            context_score * 0.30 +     # 上下文一致性30%
            behavior_score * 0.20 +    # 用户行为20%
            flow_score * 0.15 +        # 对话流15%
            time_score * 0.10          # 时间相关性10%
        )

        relevance_threshold = getattr(self.context, 'relevance_threshold', 0.6)
        return total_score >= relevance_threshold

    def _analyze_structural_features(self, message_content: str) -> float:
        """分析消息的结构化特征"""
        if not message_content or not message_content.strip():
            return 0.0

        score = 0.0
        content = message_content.strip()

        # 长度特征（适中长度更可能需要回复）
        length = len(content)
        if 10 <= length <= 150:
            score += 0.3  # 适中长度
        elif length < 10:
            score += 0.1  # 太短
        else:
            score += 0.2  # 较长但仍可能重要

        # 标点符号密度（丰富的标点可能表示更正式或更需要回复的内容）
        punctuation_count = sum(1 for char in content if char in "，。！？；：""''（）【】")
        punctuation_ratio = punctuation_count / length if length > 0 else 0
        if 0.05 <= punctuation_ratio <= 0.25:
            score += 0.3
        elif punctuation_ratio > 0.25:
            score += 0.2

        # 特殊符号分析
        if "@" in content:
            score += 0.4  # @机器人直接相关

        # 疑问句特征
        question_indicators = ["吗", "呢", "啊", "吧", "?", "？", "怎么", "什么", "为什么", "怎么"]
        if any(indicator in content for indicator in question_indicators):
            score += 0.3

        # 情感表达特征
        emotion_indicators = ["!", "！", "😊", "😂", "👍", "❤️", "😭", "😤", "🤔"]
        if any(indicator in content for indicator in emotion_indicators):
            score += 0.2

        return min(1.0, score)

    def _analyze_context_consistency(self, message_content: str, chat_context: Dict) -> float:
        """分析与上下文的一致性"""
        conversation_history = chat_context.get("conversation_history", [])
        if not conversation_history:
            return 0.5  # 没有历史上下文，给中等分数

        # 分析最近几条消息的模式
        recent_messages = conversation_history[-5:]  # 最近5条消息
        if not recent_messages:
            return 0.5

        consistency_score = 0.0

        # 1. 用户交互模式分析
        current_user = chat_context.get("user_id", "")
        recent_users = [msg.get("user_id", "") for msg in recent_messages]

        # 检查是否是连续对话
        if recent_users.count(current_user) >= 2:
            consistency_score += 0.3

        # 检查是否是回复模式
        if len(recent_users) >= 2:
            if recent_users[-2] != current_user:  # 上一条消息不是当前用户发的
                consistency_score += 0.2

        # 2. 消息长度模式分析
        current_length = len(message_content.strip())
        recent_lengths = [len(msg.get("content", "").strip()) for msg in recent_messages]

        if recent_lengths:
            avg_length = sum(recent_lengths) / len(recent_lengths)
            length_diff = abs(current_length - avg_length) / max(avg_length, 1)
            if length_diff < 0.5:  # 长度差异不大
                consistency_score += 0.2

        # 3. 时间间隔分析
        if len(recent_messages) >= 2:
            current_time = chat_context.get("timestamp", time.time())
            last_msg_time = recent_messages[-1].get("timestamp", 0)
            time_diff = current_time - last_msg_time

            if time_diff < 300:  # 5分钟内
                consistency_score += 0.3
            elif time_diff < 1800:  # 30分钟内
                consistency_score += 0.2

        return min(1.0, consistency_score)

    def _analyze_user_behavior_pattern(self, chat_context: Dict) -> float:
        """分析用户行为模式"""
        user_id = chat_context.get("user_id", "")
        if not user_id:
            return 0.5

        # 从状态管理器获取用户的历史行为数据
        if hasattr(self.state_manager, 'get_user_interaction_pattern'):
            pattern_data = self.state_manager.get_user_interaction_pattern(user_id)
        else:
            # 回退方案：基于当前上下文估算
            conversation_history = chat_context.get("conversation_history", [])
            user_messages = [msg for msg in conversation_history if msg.get("user_id") == user_id]

            pattern_data = {
                "total_messages": len(user_messages),
                "avg_response_time": 0,  # 简化处理
                "interaction_frequency": len(user_messages) / max(1, (time.time() - chat_context.get("timestamp", time.time())) / 3600)  # 每小时消息数
            }

        # 基于行为模式计算相关性分数
        score = 0.0

        # 高频互动用户
        if pattern_data.get("interaction_frequency", 0) > 2:  # 每小时超过2条消息
            score += 0.3

        # 近期活跃用户
        last_activity = pattern_data.get("last_activity", 0)
        if time.time() - last_activity < 3600:  # 1小时内活跃
            score += 0.3

        # 消息质量模式
        avg_length = pattern_data.get("avg_message_length", 50)
        if 20 <= avg_length <= 200:  # 适中长度的消息
            score += 0.2

        # 互动响应模式
        response_rate = pattern_data.get("response_rate", 0.5)
        if response_rate > 0.7:  # 高响应率
            score += 0.2

        return min(1.0, score)

    def _analyze_conversation_flow(self, chat_context: Dict) -> float:
        """分析对话流"""
        conversation_history = chat_context.get("conversation_history", [])
        if len(conversation_history) < 2:
            return 0.5

        flow_score = 0.0

        # 1. 对话节奏分析
        recent_messages = conversation_history[-10:]
        if len(recent_messages) >= 3:
            # 计算消息间隔
            intervals = []
            for i in range(1, len(recent_messages)):
                interval = recent_messages[i].get("timestamp", 0) - recent_messages[i-1].get("timestamp", 0)
                intervals.append(interval)

            if intervals:
                avg_interval = sum(intervals) / len(intervals)
                current_interval = chat_context.get("timestamp", time.time()) - recent_messages[-1].get("timestamp", 0)

                # 如果当前间隔接近平均间隔，说明对话节奏正常
                if abs(current_interval - avg_interval) / max(avg_interval, 1) < 0.5:
                    flow_score += 0.3

        # 2. 话题连贯性分析
        # 简单分析：检查是否有重复的用户交互模式
        user_sequence = [msg.get("user_id", "") for msg in recent_messages]
        transitions = []
        for i in range(len(user_sequence) - 1):
            transitions.append((user_sequence[i], user_sequence[i + 1]))

        # 分析转换模式
        if transitions:
            # 检查是否有重复的交互模式
            unique_transitions = set(transitions)
            if len(unique_transitions) < len(transitions) * 0.7:  # 如果有很多重复的交互模式
                flow_score += 0.4

        return min(1.0, flow_score)

    def _analyze_temporal_relevance(self, chat_context: Dict) -> float:
        """分析时间相关性"""
        current_time = time.time()
        conversation_history = chat_context.get("conversation_history", [])

        if not conversation_history:
            return 0.5

        # 分析消息的时间分布
        recent_messages = conversation_history[-20:]  # 最近20条消息
        if len(recent_messages) < 3:
            return 0.5

        # 计算消息的时间间隔
        intervals = []
        for i in range(1, len(recent_messages)):
            interval = recent_messages[i].get("timestamp", 0) - recent_messages[i-1].get("timestamp", 0)
            if interval > 0:
                intervals.append(interval)

        if not intervals:
            return 0.5

        # 分析时间模式
        avg_interval = sum(intervals) / len(intervals)
        std_dev = (sum((x - avg_interval) ** 2 for x in intervals) / len(intervals)) ** 0.5

        # 计算当前消息的时间相关性
        last_msg_time = recent_messages[-1].get("timestamp", 0)
        current_interval = current_time - last_msg_time

        # 如果当前间隔接近平均间隔，说明时间相关性高
        if abs(current_interval - avg_interval) <= std_dev:
            return 0.8
        elif abs(current_interval - avg_interval) <= std_dev * 2:
            return 0.6
        else:
            return 0.3
    
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
