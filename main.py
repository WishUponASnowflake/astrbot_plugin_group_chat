import asyncio
import json
import time
from typing import Dict, List, Any

from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.api.message_components import Plain

# 导入我们自定义的核心模块
from .core.chat_manager import GroupChatManager
from .core.mode_manager import ModeManager
from .config.plugin_config import PluginConfig

@register("astrbot_plugin_group_chat", "qa296", "一个高级群聊交互插件，能像真人一样主动参与对话，实现拟人化的主动交互体验。", "1.0.0", "https://github.com/your-repo/astrbot_plugin_group_chat")
class GroupChatPlugin(Star):
    def __init__(self, context: Context, config: Dict[str, Any] = {}):
        super().__init__(context)
        
        # 加载插件配置
        self.plugin_config = PluginConfig(config)
        logger.info(f"插件配置已加载: {self.plugin_config.to_dict()}")

        # 初始化核心管理器
        self.chat_manager = GroupChatManager(self.context, self.plugin_config)
        self.mode_manager = ModeManager(self.context, self.plugin_config, self.chat_manager)
        
        logger.info("astrbot_plugin_group_chat 插件已成功加载。")

    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    async def handle_group_message(self, event: AstrMessageEvent):
        """处理所有群聊消息的主入口点。"""
        # 将消息传递给模式管理器，由它决定如何处理
        await self.mode_manager.process_message(event)


    async def terminate(self):
        """插件被卸载/停用时调用，用于清理资源。"""
        logger.info("astrbot_plugin_group_chat 插件正在终止，执行清理操作...")
        # 在这里可以添加任何必要的清理逻辑，例如保存状态、关闭连接等
        logger.info("astrbot_plugin_group_chat 插件已成功终止。")
