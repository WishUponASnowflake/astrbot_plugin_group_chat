import time
import math
import re
from typing import Any, Dict

from astrbot.api import logger
from astrbot.api.star import Context
from state_manager import StateManager
from impression_manager import ImpressionManager

try:
    import jieba
    HAS_JIEBA = True
except ImportError:
    HAS_JIEBA = False
    logger.info("jieba 未安装，使用内置分词")

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

        # 心流节奏融入：基于时间间隔动态调整阈值
        dynamic_threshold = self._calculate_dynamic_threshold(event, chat_context, willingness_threshold)

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
                    "interaction_mode": chat_context.get("current_mode", "normal"),
                    "dynamic_threshold": dynamic_threshold
                }
            }
        else:
            # 应用动态阈值（心流节奏）
            should_respond = final_willingness >= dynamic_threshold
            return {
                "should_respond": should_respond,
                "willingness_score": final_willingness,
                "requires_llm_decision": False,
                "decision_context": {
                    "base_willingness": final_willingness,
                    "original_threshold": willingness_threshold,
                    "dynamic_threshold": dynamic_threshold
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
        group_id = chat_context.get("group_id", "default")

        bonus = 0.0

        # 1. 检查是否与同一用户连续对话（原有逻辑）
        if len(conversation_history) >= 2:
            last_two = conversation_history[-2:]
            if all(msg.get("user_id") == user_id for msg in last_two):
                bonus += 0.2  # 连续对话奖励

        # 2. 融入相似度计算：检查与最近机器人回复的相似度
        if len(conversation_history) >= 1:
            # 找到最近的机器人回复
            last_bot_reply = None
            for msg in reversed(conversation_history):
                if msg.get("role") == "assistant":
                    last_bot_reply = msg.get("content", "")
                    break

            if last_bot_reply:
                # 获取当前消息（假设是conversation_history的最后一个）
                current_msg = conversation_history[-1] if conversation_history else None
                if current_msg and current_msg.get("role") == "user":
                    current_content = current_msg.get("content", "")
                    # 计算相似度
                    similarity = self._hf_similarity(last_bot_reply, current_content, group_id)
                    # 相似度奖励：0.7以上给0.3，0.5-0.7给0.15
                    if similarity >= 0.7:
                        bonus += 0.3
                    elif similarity >= 0.5:
                        bonus += 0.15

        return min(0.5, bonus)  # 最高奖励0.5
    
    def _calculate_fatigue_penalty(self, user_id: str, chat_context: Dict) -> float:
        """计算疲劳度惩罚"""
        fatigue_data = self.state_manager.get_fatigue_data()
        user_fatigue = fatigue_data.get(user_id, 0)

        # 根据疲劳度计算惩罚
        fatigue_threshold = getattr(self.config, 'fatigue_threshold', 5)
        if user_fatigue >= fatigue_threshold:
            return 0.5  # 高疲劳度惩罚

        return user_fatigue * 0.05  # 线性疲劳惩罚

    def _calculate_dynamic_threshold(self, event: Any, chat_context: Dict, base_threshold: float) -> float:
        """计算动态阈值（心流节奏融入）"""
        group_id = event.get_group_id()
        if not group_id:
            return base_threshold

        # 获取心流状态
        state = self._hf_get_state(group_id)
        current_time = time.time()
        conversation_history = chat_context.get("conversation_history", [])

        # 基础冷却时间（45秒）
        cooldown = 45.0

        # 根据活跃度调整冷却时间（活跃时适当缩短）
        recent_count = sum(1 for msg in conversation_history
                          if current_time - msg.get("timestamp", 0) < 60)
        activity_factor = min(1.0, recent_count / 5.0)  # 每分钟最多5条消息为基准
        cooldown = cooldown * (1.0 - 0.3 * activity_factor)

        # 检查时间间隔
        dt = current_time - state.get("last_reply_ts", 0)
        if dt < cooldown:
            # 距离上次回复太近，提高阈值（减少回复概率）
            time_penalty = (cooldown - dt) / cooldown * 0.2
            return min(0.9, base_threshold + time_penalty)

        # @提及降低阈值
        if self._hf_is_at_me(event):
            return max(0.1, base_threshold - 0.1)

        # 连续回复数提高阈值
        streak = state.get("streak", 0)
        if streak > 0:
            streak_penalty = min(0.2, streak * 0.05)
            return min(0.9, base_threshold + streak_penalty)

        return base_threshold

    # 心流算法相关方法
    def _hf_get_state(self, group_id: str) -> Dict:
        """获取心流状态"""
        key = f"heartflow:{group_id}"
        state = self.state_manager.get(key, {})
        if not state:
            state = {
                "energy": 0.8,  # 初始能量
                "last_reply_ts": 0.0,
                "streak": 0
            }
            self.state_manager.set(key, state)
        return state

    def _hf_save_state(self, group_id: str, state: Dict):
        """保存心流状态"""
        key = f"heartflow:{group_id}"
        self.state_manager.set(key, state)

    def _hf_norm_count_last_seconds(self, conversation_history: list, seconds: int) -> float:
        """计算最近N秒内的消息数量并归一化"""
        current_time = time.time()
        recent_count = sum(1 for msg in conversation_history
                          if current_time - msg.get("timestamp", 0) < seconds)
        # 归一化：假设每分钟最多5条消息为活跃
        return min(1.0, recent_count / (seconds / 60 * 5))

    def _hf_is_at_me(self, event: Any) -> bool:
        """检查消息是否@机器人"""
        try:
            # 检查消息链中是否有At组件指向机器人
            if hasattr(event, 'message_obj') and hasattr(event.message_obj, 'message'):
                for comp in event.message_obj.message:
                    if hasattr(comp, 'type') and comp.type == 'at':
                        if hasattr(comp, 'qq') and str(comp.qq) == str(event.get_self_id()):
                            return True
            # 回退：检查文本中是否包含@机器人昵称
            message_str = getattr(event, 'message_str', '')
            bot_nickname = getattr(event, 'get_self_nickname', lambda: '')()
            if bot_nickname and f"@{bot_nickname}" in message_str:
                return True
        except Exception:
            pass
        return False

    def _hf_similarity(self, a: str, b: str, group_id: str) -> float:
        """计算两段文本的相似度（学习Wakepro）"""
        if not a or not b:
            return 0.0

        # 分词处理
        if HAS_JIEBA:
            words_a = list(jieba.cut(a))
            words_b = list(jieba.cut(b))
        else:
            # 无jieba时使用简单正则分词
            words_a = re.findall(r'[\u4e00-\u9fa5]+|[a-zA-Z]+|\d+', a)
            words_b = re.findall(r'[\u4e00-\u9fa5]+|[a-zA-Z]+|\d+', b)

        # 过滤停用词和单字
        stop_words = {"的", "了", "在", "是", "和", "与", "或", "这", "那", "我", "你", "他", "她", "它"}
        words_a = [w for w in words_a if len(w) > 1 and w not in stop_words]
        words_b = [w for w in words_b if len(w) > 1 and w not in stop_words]

        if not words_a or not words_b:
            return 0.0

        # 计算词频向量
        from collections import Counter
        vec_a = Counter(words_a)
        vec_b = Counter(words_b)

        # 计算余弦相似度
        intersection = set(vec_a.keys()) & set(vec_b.keys())
        numerator = sum(vec_a[word] * vec_b[word] for word in intersection)

        norm_a = math.sqrt(sum(count ** 2 for count in vec_a.values()))
        norm_b = math.sqrt(sum(count ** 2 for count in vec_b.values()))

        if norm_a == 0 or norm_b == 0:
            return 0.0

        cosine = numerator / (norm_a * norm_b)
        # 使用sigmoid函数将结果映射到更合理的范围
        return 1 / (1 + math.exp(-8 * (cosine - 0.6)))

    def _hf_on_user_msg(self, event: Any, chat_context: Dict):
        """用户消息到达时的心流状态更新"""
        group_id = event.get_group_id()
        if not group_id:
            return

        state = self._hf_get_state(group_id)
        conversation_history = chat_context.get("conversation_history", [])

        # 基础恢复
        state["energy"] = min(1.0, state["energy"] + 0.01)

        # 活跃度加成
        mlm_norm = self._hf_norm_count_last_seconds(conversation_history, 60)
        state["energy"] = min(1.0, state["energy"] + 0.06 * mlm_norm)

        # @提及加成
        if self._hf_is_at_me(event):
            state["energy"] = min(1.0, state["energy"] + 0.10)

        # 连续性加成：与最近机器人回复的相似度
        last_bot_reply = None
        for msg in reversed(conversation_history):
            if msg.get("role") == "assistant":
                last_bot_reply = msg.get("content", "")
                break

        if last_bot_reply:
            continuity = self._hf_similarity(last_bot_reply, event.message_str, group_id)
            state["energy"] = min(1.0, state["energy"] + 0.08 * continuity)

        # 确保能量不低于最小值
        state["energy"] = max(0.1, state["energy"])

        self._hf_save_state(group_id, state)

    def _hf_can_pass_gate(self, event: Any, chat_context: Dict) -> bool:
        """检查是否可以通过心流门控"""
        group_id = event.get_group_id()
        if not group_id:
            return True  # 私聊或其他情况默认通过

        state = self._hf_get_state(group_id)
        current_time = time.time()
        conversation_history = chat_context.get("conversation_history", [])

        # 计算动态冷却时间
        mlm_norm = self._hf_norm_count_last_seconds(conversation_history, 60)
        cooldown = 45.0 * (1.0 - 0.3 * mlm_norm)  # 活跃时适当缩短冷却

        # 检查时间间隔
        dt = current_time - state["last_reply_ts"]
        if dt < cooldown:
            return False

        # 计算动态阈值
        threshold = 0.35

        # @提及降低阈值
        if self._hf_is_at_me(event):
            threshold -= 0.1

        # 连续性降低阈值
        last_bot_reply = None
        for msg in reversed(conversation_history):
            if msg.get("role") == "assistant":
                last_bot_reply = msg.get("content", "")
                break

        if last_bot_reply:
            continuity = self._hf_similarity(last_bot_reply, event.message_str, group_id)
            if continuity >= 0.75:
                threshold -= 0.05

        # 连续回复数提高阈值
        threshold += 0.05 * state["streak"]
        threshold = min(0.7, threshold)  # 最高阈值限制

        # 检查能量
        return state["energy"] >= threshold

    def on_bot_reply_update(self, event: Any, reply_len: int):
        """机器人回复成功后的心流状态更新"""
        group_id = event.get_group_id()
        if not group_id:
            return

        state = self._hf_get_state(group_id)
        current_time = time.time()

        # 基础消耗
        state["energy"] = max(0.1, state["energy"] - 0.10)

        # 回复长度消耗
        len_penalty = 0.05 * min(1.0, reply_len / 200)  # 200字为基准
        state["energy"] = max(0.1, state["energy"] - len_penalty)

        # 连续回复惩罚
        streak_penalty = 0.04 * state["streak"]
        state["energy"] = max(0.1, state["energy"] - streak_penalty)

        # 更新状态
        state["last_reply_ts"] = current_time
        state["streak"] += 1

        self._hf_save_state(group_id, state)
