"""
AstrBot Group Chat Plugin - Memory Integration
记忆系统集成模块，用于与MemoraConnectPlugin交互
"""

import time
from typing import Dict, List, Any, Optional, TYPE_CHECKING

from astrbot.api.event import AstrMessageEvent
from astrbot.api import logger

from .chat_manager import UserState, GroupState, ThinkingContext

if TYPE_CHECKING:
    from astrbot.api.star import Context
    from ..config.plugin_config import PluginConfig


class MemoryIntegration:
    """记忆系统集成"""
    
    def __init__(self, plugin_config: "PluginConfig", context: "Context"):
        self.config: "PluginConfig" = plugin_config
        self.context: "Context" = context
        
        # MemoraConnectPlugin实例缓存
        self.memora_plugin: Optional[Any] = None
        self.plugin_checked = False
        
        logger.info("MemoryIntegration 初始化完成")
    
    def _get_memora_plugin(self):
        """获取MemoraConnectPlugin实例"""
        if self.plugin_checked:
            return self.memora_plugin
        
        try:
            # 获取MemoraConnectPlugin插件实例
            memora_plugin_meta = self.context.get_registered_star("astrbot_plugin_memora_connect")
            if memora_plugin_meta:
                self.memora_plugin = memora_plugin_meta.star_cls
                logger.info("成功获取MemoraConnectPlugin实例")
            else:
                logger.warning("未找到MemoraConnectPlugin插件")
            
            self.plugin_checked = True
            return self.memora_plugin
            
        except Exception as e:
            logger.error(f"获取MemoraConnectPlugin实例时发生错误: {e}")
            self.plugin_checked = True
            return None
    
    async def get_memory_context(self, event: AstrMessageEvent, user_state: UserState, 
                               group_state: GroupState) -> Optional[Dict[str, Any]]:
        """获取记忆上下文"""
        if not self.config.enable_memory_integration:
            return None
        
        try:
            memora_plugin = self._get_memora_plugin()
            if not memora_plugin:
                return None
            
            user_id = event.get_sender_id()
            group_id = event.get_group_id()
            message_content = event.message_str
            
            # 获取对用户的印象摘要
            impression = await self._get_user_impression(memora_plugin, user_id, group_id)
            
            # 回忆相关记忆
            memories = await self._recall_relevant_memories(
                memora_plugin, message_content, user_id, group_id
            )
            
            # 计算记忆影响
            memory_influence = self._calculate_memory_influence(impression, memories)
            
            return {
                "impression": impression,
                "memories": memories,
                "influence": memory_influence,
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"获取记忆上下文时发生错误: {e}")
            return None
    
    async def _get_user_impression(self, memora_plugin: Any, user_id: str, group_id: str) -> Dict[str, Any]:
        """获取用户印象摘要"""
        try:
            # 调用MemoraConnectPlugin的API
            impression = await memora_plugin.get_impression_summary_api(
                user_id=user_id,
                group_id=group_id
            )
            
            return impression or {}
            
        except Exception as e:
            logger.error(f"获取用户印象时发生错误: {e}")
            return {}
    
    async def _recall_relevant_memories(self, memora_plugin: Any, message_content: str, 
                                      user_id: str, group_id: str) -> List[Dict[str, Any]]:
        """回忆相关记忆"""
        try:
            # 提取关键词
            keywords = self._extract_keywords(message_content)
            
            memories = []
            for keyword in keywords[:3]:  # 限制关键词数量
                # 调用MemoraConnectPlugin的API
                keyword_memories = await memora_plugin.recall_memories_api(
                    keyword=keyword,
                    group_id=group_id,
                    limit=self.config.memory_recall_limit
                )
                
                if keyword_memories:
                    memories.extend(keyword_memories)
            
            # 去重并限制数量
            unique_memories = []
            seen_ids = set()
            
            for memory in memories:
                memory_id = memory.get("id", "")
                if memory_id and memory_id not in seen_ids:
                    seen_ids.add(memory_id)
                    unique_memories.append(memory)
            
            return unique_memories[:self.config.memory_recall_limit]
            
        except Exception as e:
            logger.error(f"回忆相关记忆时发生错误: {e}")
            return []
    
    def _extract_keywords(self, message_content: str) -> List[str]:
        """从消息内容中提取关键词"""
        try:
            # 简单的关键词提取逻辑
            words = message_content.split()
            keywords = []
            
            for word in words:
                # 过滤掉太短的词
                if len(word) >= 2:
                    # 去除标点符号
                    clean_word = word.strip("，。！？；：""''（）【】")
                    if clean_word:
                        keywords.append(clean_word)
            
            return keywords
            
        except Exception as e:
            logger.error(f"提取关键词时发生错误: {e}")
            return []
    
    def _calculate_memory_influence(self, impression: Dict[str, Any], 
                                 memories: List[Dict[str, Any]]) -> float:
        """计算记忆影响分数"""
        try:
            influence = 0.0
            
            # 基于印象的影响
            if impression:
                # 如果印象是正面的，增加影响
                sentiment = impression.get("sentiment", 0.0)
                influence += sentiment * 0.3
                
                # 如果有熟悉度，增加影响
                familiarity = impression.get("familiarity", 0.0)
                influence += familiarity * 0.2
            
            # 基于记忆数量的影响
            memory_count = len(memories)
            influence += min(memory_count * 0.1, 0.3)
            
            # 基于记忆相关性的影响
            if memories:
                avg_relevance = sum(m.get("relevance", 0.5) for m in memories) / len(memories)
                influence += avg_relevance * 0.2
            
            return max(0.0, min(1.0, influence))
            
        except Exception as e:
            logger.error(f"计算记忆影响时发生错误: {e}")
            return 0.0
    
    async def add_interaction_memory(self, context: ThinkingContext, reply_content: str):
        """添加交互记忆"""
        if not self.config.enable_memory_integration:
            return
        
        try:
            memora_plugin = self._get_memora_plugin()
            if not memora_plugin:
                return
            
            user_id = context.event.get_sender_id()
            group_id = context.event.get_group_id()
            message_content = context.event.message_str
            
            # 构建记忆内容
            memory_content = {
                "user_message": message_content,
                "bot_reply": reply_content,
                "interest_score": context.interest_score,
                "timestamp": time.time(),
                "context": {
                    "group_chat_heat": context.group_state.chat_heat,
                    "conversation_streak": context.user_state.conversation_streak,
                    "fatigue_level": context.user_state.fatigue_level
                }
            }
            
            # 调用MemoraConnectPlugin的API添加记忆
            await memora_plugin.add_memory_api(
                content=str(memory_content),
                user_id=user_id,
                group_id=group_id,
                tags=["interaction", "group_chat"]
            )
            
            logger.debug("成功添加交互记忆")
            
        except Exception as e:
            logger.error(f"添加交互记忆时发生错误: {e}")
    
    async def update_user_impression(self, context: ThinkingContext, interaction_result: str):
        """更新用户印象"""
        if not self.config.enable_memory_integration:
            return
        
        try:
            memora_plugin = self._get_memora_plugin()
            if not memora_plugin:
                return
            
            user_id = context.event.get_sender_id()
            group_id = context.event.get_group_id()
            
            # 基于交互结果更新印象
            impression_update = {
                "last_interaction": time.time(),
                "interaction_result": interaction_result,
                "interest_score": context.interest_score,
                "conversation_streak": context.user_state.conversation_streak
            }
            
            # 这里可以调用MemoraConnectPlugin的相关API来更新印象
            # 由于API可能不同，这里只是示例
            logger.debug(f"更新用户印象: {impression_update}")
            
        except Exception as e:
            logger.error(f"更新用户印象时发生错误: {e}")
    
    def is_memory_enabled(self) -> bool:
        """检查记忆系统是否启用"""
        return self.config.enable_memory_integration and self._get_memora_plugin() is not None
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """获取记忆系统统计信息"""
        try:
            return {
                "memory_integration_enabled": self.config.enable_memory_integration,
                "memora_plugin_available": self._get_memora_plugin() is not None,
                "memory_influence_weight": self.config.memory_influence_weight,
                "memory_recall_limit": self.config.memory_recall_limit,
                "plugin_checked": self.plugin_checked
            }
        except Exception as e:
            logger.error(f"获取记忆系统统计时发生错误: {e}")
            return {}
