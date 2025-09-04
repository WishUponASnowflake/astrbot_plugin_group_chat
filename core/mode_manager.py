"""
AstrBot Group Chat Plugin - Mode Manager
模式管理器模块，切换普通聊天和专注聊天模式
"""

import time
from typing import Dict, Any, TYPE_CHECKING

from astrbot.api.event import AstrMessageEvent
from astrbot.api import logger
from astrbot.api.star import Context

from .chat_manager import GroupChatManager, ChatMode

if TYPE_CHECKING:
    from ..config.plugin_config import PluginConfig


class ModeManager:
    """模式管理器"""
    
    def __init__(self, context: Context, plugin_config: "PluginConfig", chat_manager: GroupChatManager):
        self.context: Context = context
        self.config: "PluginConfig" = plugin_config
        self.chat_manager = chat_manager
        
        # 模式状态
        self.current_mode = ChatMode.NORMAL
        self.mode_switch_time = 0
        self.mode_history = []
        
        logger.info("ModeManager 初始化完成")
    
    async def process_message(self, event: AstrMessageEvent):
        """处理消息的主入口"""
        try:
            if not self.config.enable_plugin:
                return
            
            # 委托给聊天管理器处理
            result = await self.chat_manager.process_message(event)
            
            # 更新模式状态
            await self._update_mode_state(event)
            
            return result
            
        except Exception as e:
            logger.error(f"模式管理器处理消息时发生错误: {e}")
            return None
    
    async def _update_mode_state(self, event: AstrMessageEvent):
        """更新模式状态"""
        try:
            current_time = time.time()
            
            # 检查是否需要切换回普通模式
            if (self.current_mode == ChatMode.FOCUSED and 
                current_time - self.mode_switch_time > 300):  # 5分钟后自动切换回普通模式
                
                await self._switch_to_normal_mode()
            
        except Exception as e:
            logger.error(f"更新模式状态时发生错误: {e}")
    
    async def _switch_to_normal_mode(self):
        """切换到普通模式"""
        try:
            if self.current_mode != ChatMode.NORMAL:
                logger.info("切换到普通聊天模式")
                self.current_mode = ChatMode.NORMAL
                self.mode_switch_time = time.time()
                self.mode_history.append({
                    "mode": ChatMode.NORMAL,
                    "timestamp": self.mode_switch_time,
                    "reason": "timeout"
                })
                
        except Exception as e:
            logger.error(f"切换到普通模式时发生错误: {e}")
    
    def get_current_mode(self) -> ChatMode:
        """获取当前模式"""
        return self.current_mode
    
    def get_mode_info(self) -> Dict[str, Any]:
        """获取模式信息"""
        try:
            return {
                "current_mode": self.current_mode.value,
                "mode_switch_time": self.mode_switch_time,
                "time_since_switch": time.time() - self.mode_switch_time,
                "mode_history_count": len(self.mode_history),
                "enable_focused_chat": self.config.enable_focused_chat,
                "focused_chat_threshold": self.config.focused_chat_threshold
            }
        except Exception as e:
            logger.error(f"获取模式信息时发生错误: {e}")
            return {}
    
    def force_switch_mode(self, mode: ChatMode):
        """强制切换模式"""
        try:
            if mode != self.current_mode:
                logger.info(f"强制切换到{mode.value}模式")
                self.current_mode = mode
                self.mode_switch_time = time.time()
                self.mode_history.append({
                    "mode": mode,
                    "timestamp": self.mode_switch_time,
                    "reason": "forced"
                })
                
        except Exception as e:
            logger.error(f"强制切换模式时发生错误: {e}")
    
    def can_switch_to_focused(self) -> bool:
        """检查是否可以切换到专注模式"""
        try:
            current_time = time.time()
            cooldown_passed = (current_time - self.mode_switch_time) >= self.config.mode_switch_cooldown
            return cooldown_passed and self.config.enable_focused_chat
            
        except Exception as e:
            logger.error(f"检查是否可以切换到专注模式时发生错误: {e}")
            return False
    
    def get_mode_statistics(self) -> Dict[str, Any]:
        """获取模式统计信息"""
        try:
            mode_stats = {
                "normal_mode_time": 0,
                "focused_mode_time": 0,
                "total_switches": len(self.mode_history)
            }
            
            # 计算各模式使用时间
            for i in range(len(self.mode_history)):
                record = self.mode_history[i]
                start_time = record["timestamp"]
                
                if i < len(self.mode_history) - 1:
                    end_time = self.mode_history[i + 1]["timestamp"]
                else:
                    end_time = time.time()
                
                duration = end_time - start_time
                
                if record["mode"] == ChatMode.NORMAL:
                    mode_stats["normal_mode_time"] += duration
                elif record["mode"] == ChatMode.FOCUSED:
                    mode_stats["focused_mode_time"] += duration
            
            return mode_stats
            
        except Exception as e:
            logger.error(f"获取模式统计信息时发生错误: {e}")
            return {}
    
    def reset_mode_state(self):
        """重置模式状态"""
        try:
            self.current_mode = ChatMode.NORMAL
            self.mode_switch_time = time.time()
            self.mode_history = []
            logger.info("模式状态已重置")
            
        except Exception as e:
            logger.error(f"重置模式状态时发生错误: {e}")
