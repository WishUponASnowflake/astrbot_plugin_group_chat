"""
AstrBot Group Chat Plugin - Fatigue Manager
疲劳管理器模块，防止话痨
"""

import time
from typing import Dict, Any, TYPE_CHECKING
from dataclasses import dataclass

from astrbot.api import logger

from .chat_manager import UserState

if TYPE_CHECKING:
    from ..config.plugin_config import PluginConfig


@dataclass
class FatigueConfig:
    """疲劳配置"""
    max_replies_in_session: int = 10
    fatigue_recovery_time: int = 300
    fatigue_decay_rate: float = 0.8
    fatigue_increment: float = 0.2
    fatigue_threshold: float = 0.8


class FatigueManager:
    """疲劳管理器"""
    
    def __init__(self, plugin_config: "PluginConfig"):
        self.config: "PluginConfig" = plugin_config
        
        # 疲劳配置
        self.fatigue_config = FatigueConfig(
            max_replies_in_session=plugin_config.max_replies_in_session,
            fatigue_recovery_time=plugin_config.fatigue_recovery_time,
            fatigue_decay_rate=plugin_config.focused_fatigue_decay_rate,
            fatigue_increment=0.2,
            fatigue_threshold=0.8
        )
        
        logger.info("FatigueManager 初始化完成")
    
    def is_fatigued(self, user_state: UserState) -> bool:
        """检查用户是否处于疲劳状态"""
        try:
            # 检查连续回复次数
            if user_state.consecutive_replies >= self.fatigue_config.max_replies_in_session:
                return True
            
            # 检查疲劳程度
            if user_state.fatigue_level >= self.fatigue_config.fatigue_threshold:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"检查疲劳状态时发生错误: {e}")
            return False
    
    def update_fatigue(self, user_state: UserState) -> float:
        """更新疲劳程度"""
        try:
            current_time = time.time()
            
            # 计算时间衰减
            time_since_last_reply = current_time - user_state.last_interaction_time
            
            if time_since_last_reply > self.fatigue_config.fatigue_recovery_time:
                # 超过恢复时间，重置疲劳程度
                user_state.fatigue_level = 0.0
                user_state.consecutive_replies = 0
            else:
                # 增加疲劳程度
                fatigue_increment = self.fatigue_config.fatigue_increment
                user_state.fatigue_level += fatigue_increment
                
                # 应用疲劳衰减
                user_state.fatigue_level *= self.fatigue_config.fatigue_decay_rate
            
            # 确保疲劳程度在0-1范围内
            user_state.fatigue_level = max(0.0, min(1.0, user_state.fatigue_level))
            
            return user_state.fatigue_level
            
        except Exception as e:
            logger.error(f"更新疲劳程度时发生错误: {e}")
            return user_state.fatigue_level
    
    def get_fatigue_status(self, user_state: UserState) -> Dict[str, Any]:
        """获取疲劳状态信息"""
        try:
            return {
                "fatigue_level": user_state.fatigue_level,
                "consecutive_replies": user_state.consecutive_replies,
                "is_fatigued": self.is_fatigued(user_state),
                "max_replies": self.fatigue_config.max_replies_in_session,
                "recovery_time": self.fatigue_config.fatigue_recovery_time,
                "fatigue_threshold": self.fatigue_config.fatigue_threshold
            }
        except Exception as e:
            logger.error(f"获取疲劳状态时发生错误: {e}")
            return {}
    
    def reset_fatigue(self, user_state: UserState):
        """重置疲劳状态"""
        try:
            user_state.fatigue_level = 0.0
            user_state.consecutive_replies = 0
            logger.info("疲劳状态已重置")
        except Exception as e:
            logger.error(f"重置疲劳状态时发生错误: {e}")
    
    def calculate_recovery_time(self, user_state: UserState) -> float:
        """计算恢复时间"""
        try:
            if user_state.fatigue_level <= 0:
                return 0.0
            
            # 基于疲劳程度计算恢复时间
            recovery_time = (user_state.fatigue_level * 
                           self.fatigue_config.fatigue_recovery_time)
            
            return recovery_time
            
        except Exception as e:
            logger.error(f"计算恢复时间时发生错误: {e}")
            return 0.0
    
    def should_take_break(self, user_state: UserState) -> bool:
        """判断是否应该休息"""
        try:
            # 如果疲劳程度超过阈值，建议休息
            if user_state.fatigue_level > self.fatigue_config.fatigue_threshold:
                return True
            
            # 如果连续回复次数过多，建议休息
            if user_state.consecutive_replies > self.fatigue_config.max_replies_in_session * 0.8:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"判断是否应该休息时发生错误: {e}")
            return False
