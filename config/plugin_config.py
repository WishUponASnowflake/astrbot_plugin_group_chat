"""
AstrBot Group Chat Plugin - Plugin Configuration
插件配置管理模块
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class PluginConfig:
    """插件配置类"""
    
    # 基础配置
    enable_plugin: bool = True
    debug_mode: bool = False
    
    # 模式配置
    enable_focused_chat: bool = True
    focused_chat_threshold: float = 0.7  # 专注聊天激活阈值
    mode_switch_cooldown: int = 30  # 模式切换冷却时间(秒)
    
    # 回复意愿配置 - 经典模式
    classic_mode_enabled: bool = True
    classic_base_willingness: float = 0.3  # 基础回复意愿
    classic_at_boost: float = 0.8  # 被@时的意愿提升
    classic_topic_interest_boost: float = 0.5  # 感兴趣话题的意愿提升
    classic_reply_decay: float = 0.7  # 回复后的意愿衰减
    classic_time_decay_rate: float = 0.95  # 时间衰减率
    
    # 回复意愿配置 - 专注模式
    focused_mode_enabled: bool = True
    focused_base_willingness: float = 0.4  # 基础回复意愿
    focused_personal_factor: float = 0.6  # 个人化因素权重
    focused_chat_heat_factor: float = 0.3  # 群聊热度因素权重
    focused_conversation_factor: float = 0.5  # 连续对话因素权重
    focused_frequency_factor: float = 0.2  # 说话频率因素权重
    focused_fatigue_threshold: int = 5  # 疲劳阈值
    focused_fatigue_decay_rate: float = 0.8  # 疲劳衰减率
    
    # 兴趣度评估配置
    interest_evaluator_enabled: bool = True
    interest_threshold: float = 0.5  # 兴趣度阈值
    keyword_weight: float = 0.4  # 关键词权重
    context_weight: float = 0.3  # 上下文权重
    sender_weight: float = 0.2  # 发送者权重
    time_weight: float = 0.1  # 时间权重
    
    # 疲劳管理配置
    fatigue_manager_enabled: bool = True
    max_replies_in_session: int = 10  # 单次会话最大回复数
    fatigue_recovery_time: int = 300  # 疲劳恢复时间(秒)
    typing_simulation_enabled: bool = True  # 启用打字模拟
    typing_min_delay: float = 1.0  # 最小打字延迟(秒)
    typing_max_delay: float = 3.0  # 最大打字延迟(秒)
    
    # 回复生成配置
    reply_generator_enabled: bool = True
    reply_mode: str = "responder"  # responder 或 expresser
    expresser_thinking_enabled: bool = True  # 启用表达器思考过程
    max_reply_length: int = 500  # 最大回复长度
    enable_emoji: bool = True  # 启用表情符号
    
    # 记忆系统集成配置
    enable_memory_integration: bool = False  # 默认关闭记忆系统
    memory_influence_weight: float = 0.3  # 记忆系统影响权重
    memory_recall_limit: int = 3  # 记忆回忆数量限制
    
    # 高级配置
    response_probability_multiplier: float = 1.0  # 回复概率倍数
    experimental_features: bool = False  # 实验性功能
    
    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        """初始化配置"""
        if config_dict:
            self._update_from_dict(config_dict)
    
    def _update_from_dict(self, config_dict: Dict[str, Any]):
        """从字典更新配置"""
        for key, value in config_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'enable_plugin': self.enable_plugin,
            'debug_mode': self.debug_mode,
            'enable_focused_chat': self.enable_focused_chat,
            'focused_chat_threshold': self.focused_chat_threshold,
            'mode_switch_cooldown': self.mode_switch_cooldown,
            'classic_mode_enabled': self.classic_mode_enabled,
            'classic_base_willingness': self.classic_base_willingness,
            'classic_at_boost': self.classic_at_boost,
            'classic_topic_interest_boost': self.classic_topic_interest_boost,
            'classic_reply_decay': self.classic_reply_decay,
            'classic_time_decay_rate': self.classic_time_decay_rate,
            'focused_mode_enabled': self.focused_mode_enabled,
            'focused_base_willingness': self.focused_base_willingness,
            'focused_personal_factor': self.focused_personal_factor,
            'focused_chat_heat_factor': self.focused_chat_heat_factor,
            'focused_conversation_factor': self.focused_conversation_factor,
            'focused_frequency_factor': self.focused_frequency_factor,
            'focused_fatigue_threshold': self.focused_fatigue_threshold,
            'focused_fatigue_decay_rate': self.focused_fatigue_decay_rate,
            'interest_evaluator_enabled': self.interest_evaluator_enabled,
            'interest_threshold': self.interest_threshold,
            'keyword_weight': self.keyword_weight,
            'context_weight': self.context_weight,
            'sender_weight': self.sender_weight,
            'time_weight': self.time_weight,
            'fatigue_manager_enabled': self.fatigue_manager_enabled,
            'max_replies_in_session': self.max_replies_in_session,
            'fatigue_recovery_time': self.fatigue_recovery_time,
            'typing_simulation_enabled': self.typing_simulation_enabled,
            'typing_min_delay': self.typing_min_delay,
            'typing_max_delay': self.typing_max_delay,
            'reply_generator_enabled': self.reply_generator_enabled,
            'reply_mode': self.reply_mode,
            'expresser_thinking_enabled': self.expresser_thinking_enabled,
            'max_reply_length': self.max_reply_length,
            'enable_emoji': self.enable_emoji,
            'enable_memory_integration': self.enable_memory_integration,
            'memory_influence_weight': self.memory_influence_weight,
            'memory_recall_limit': self.memory_recall_limit,
            'response_probability_multiplier': self.response_probability_multiplier,
            'experimental_features': self.experimental_features
        }
    
    def get_mode_config(self, mode: str) -> Dict[str, Any]:
        """获取特定模式的配置"""
        if mode == "classic":
            return {
                'base_willingness': self.classic_base_willingness,
                'at_boost': self.classic_at_boost,
                'topic_interest_boost': self.classic_topic_interest_boost,
                'reply_decay': self.classic_reply_decay,
                'time_decay_rate': self.classic_time_decay_rate
            }
        elif mode == "focused":
            return {
                'base_willingness': self.focused_base_willingness,
                'personal_factor': self.focused_personal_factor,
                'chat_heat_factor': self.focused_chat_heat_factor,
                'conversation_factor': self.focused_conversation_factor,
                'frequency_factor': self.focused_frequency_factor,
                'fatigue_threshold': self.focused_fatigue_threshold,
                'fatigue_decay_rate': self.focused_fatigue_decay_rate
            }
        else:
            return {}
    
    def is_mode_enabled(self, mode: str) -> bool:
        """检查模式是否启用"""
        if mode == "classic":
            return self.classic_mode_enabled
        elif mode == "focused":
            return self.focused_mode_enabled
        else:
            return False
