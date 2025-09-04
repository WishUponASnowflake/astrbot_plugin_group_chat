"""
AstrBot Group Chat Plugin - Core Types
核心模块的共享数据类型
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any

# 从 astrbot.api.event 导入 AstrMessageEvent 以解决 ThinkingContext 中的类型提示问题
# 但为了避免再次引入循环依赖，这里使用字符串前向引用
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from astrbot.api.event import AstrMessageEvent


# 从 chat_manager.py 移动过来的类型
class ChatMode(Enum):
    """聊天模式枚举"""
    NORMAL = "normal"  # 普通聊天模式
    FOCUSED = "focused"  # 专注聊天模式


class WillingnessMode(Enum):
    """回复意愿模式枚举"""
    CLASSIC = "classic"  # 经典模式
    FOCUSED = "focused"  # 专注模式


@dataclass
class UserState:
    """用户状态"""
    user_id: str
    group_id: str
    willingness: float = 0.5  # 回复意愿
    last_interaction_time: float = 0.0  # 最后交互时间
    reply_count: int = 0  # 回复次数
    fatigue_level: float = 0.0  # 疲劳程度
    consecutive_replies: int = 0  # 连续回复次数
    conversation_streak: int = 0  # 连续对话计数
    personal_interest: float = 0.5  # 个人兴趣度


@dataclass
class GroupState:
    """群组状态"""
    group_id: str
    chat_heat: float = 0.0  # 群聊热度
    active_users: List[str] = field(default_factory=list)  # 活跃用户
    last_message_time: float = 0.0  # 最后消息时间
    message_count: int = 0  # 消息计数
    current_mode: ChatMode = ChatMode.NORMAL  # 当前模式
    mode_switch_time: float = 0.0  # 模式切换时间


@dataclass
class ThinkingContext:
    """思考上下文"""
    event: 'AstrMessageEvent'
    user_state: UserState
    group_state: GroupState
    interest_score: float
    memory_context: Optional[Dict[str, Any]] = None
    thinking_material: Dict[str, Any] = field(default_factory=dict)


# 从 interest_evaluator.py 移动过来的类型
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
