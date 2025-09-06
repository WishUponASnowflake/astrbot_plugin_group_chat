from typing import Any, List
import logging

from astrbot.api import logger

class MemoryIntegration:
    """记忆系统集成 - 只读"""
    
    def __init__(self, context: Any, config: Any):
        self.context = context
        self.config = config
        self.memora_plugin = self._init_memora_plugin()
    
    def _init_memora_plugin(self) -> Any:
        """初始化 MemoraConnectPlugin 连接"""
        try:
            memora_plugin_meta = self.context.get_registered_star("astrbot_plugin_memora_connect")
            if memora_plugin_meta:
                return memora_plugin_meta.star_cls
            else:
                logger.warning("未找到 MemoraConnectPlugin，记忆功能将不可用")
                return None
        except Exception as e:
            logger.error(f"初始化 MemoraConnectPlugin 失败: {e}")
            return None
    
    async def recall_memories(self, keywords: str, group_id: str = None, limit: int = None) -> List:
        """回忆相关记忆"""
        if not getattr(self.config, 'memory_enabled', True) or not self.memora_plugin:
            return []
        
        try:
            max_limit = limit or getattr(self.config, 'max_memories_recall', 10)
            return await self.memora_plugin.recall_memories_api(
                keywords=keywords,
                group_id=group_id,
                limit=max_limit
            )
        except Exception as e:
            logger.error(f"回忆记忆失败: {e}")
            return []
