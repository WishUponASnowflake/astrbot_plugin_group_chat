"""
AstrBot Group Chat Plugin - Reply Generator
回复生成器模块，调用LLM生成灵活的回复
"""

import random
from typing import Dict, List, Any, Optional, TYPE_CHECKING

from astrbot.api.event import AstrMessageEvent
from astrbot.api import logger
from astrbot.api.star import Context

if TYPE_CHECKING:
    from .chat_manager import ThinkingContext
    from ..config.plugin_config import PluginConfig


class ReplyGenerator:
    """回复生成器"""

    def __init__(self, plugin_config: "PluginConfig", context: Context):
        self.config: "PluginConfig" = plugin_config
        self.context: Context = context  # 存储核心上下文

        # 表情符号（可选添加）
        self.emojis = ["😊", "🙂", "😄", "👍", "✨", "🤔", "💭", "😌", "🤗", "🎉"]

        logger.info("ReplyGenerator 初始化完成")

    async def generate_reply(self, context: "ThinkingContext", reply_mode: str,
                           processing_result: Dict[str, Any]) -> Optional[str]:
        """生成回复的主入口（专注模式）"""
        try:
            prompt = self._build_prompt(context, processing_result)
            system_prompt = await self._get_system_prompt(context.event)

            # 调用LLM生成回复
            llm_response = await context.event.request_llm(
                prompt=prompt,
                system_prompt=system_prompt
            )

            reply_content = llm_response.completion_text if llm_response else None

            if reply_content:
                return self._post_process_reply(reply_content, context)
            
            return None
                
        except Exception as e:
            logger.error(f"生成专注回复时发生错误: {e}")
            return None
    
    async def generate_simple_reply(self, context: "ThinkingContext") -> Optional[str]:
        """生成简单回复（用于普通聊天模式）"""
        try:
            prompt = self._build_simple_prompt(context)
            system_prompt = await self._get_system_prompt(context.event)

            # 调用LLM生成回复
            llm_response = await context.event.request_llm(
                prompt=prompt,
                system_prompt=system_prompt
            )

            reply_content = llm_response.completion_text if llm_response else None

            if reply_content:
                return self._post_process_reply(reply_content, context)
            
            return None
            
        except Exception as e:
            logger.error(f"生成简单回复失败: {e}")
            return None

    async def _get_system_prompt(self, event: AstrMessageEvent) -> str:
        """获取当前会话的人格（System Prompt）"""
        try:
            uid = event.unified_msg_origin
            conv_manager = self.context.conversation_manager
            
            curr_cid = await conv_manager.get_curr_conversation_id(uid)
            if not curr_cid:
                # 如果没有当前对话，使用默认人格
                default_persona = self.context.provider_manager.selected_default_persona
                return default_persona.get("prompt", "") if default_persona else ""

            conversation = await conv_manager.get_conversation(uid, curr_cid)
            if not conversation or not conversation.persona_id or conversation.persona_id == "[%None]":
                # 如果对话不存在，或没有设置人格，或已取消人格，则使用默认人格
                default_persona = self.context.provider_manager.selected_default_persona
                return default_persona.get("prompt", "") if default_persona else ""

            # 获取指定的人格
            persona = self.context.provider_manager.get_persona_by_id(conversation.persona_id)
            return persona.prompt if persona else ""
            
        except Exception as e:
            logger.error(f"获取 System Prompt 失败: {e}")
            return ""

    def _build_prompt(self, context: "ThinkingContext", processing_result: Dict[str, Any]) -> str:
        """为专注模式构建LLM提示"""
        sender_name = context.event.get_sender_name()
        message = context.event.message_str
        
        prompt = f"""你是一个群聊机器人，正在参与一个群聊。
当前群聊热度为 {context.group_state.chat_heat:.2f} (0表示冷清, 1表示火热)。
你对发送者 {sender_name} 的个人兴趣度为 {context.user_state.personal_interest:.2f}。
你与 {sender_name} 的连续对话次数为 {context.user_state.conversation_streak}。

这是你对当前消息的分析材料:
{processing_result}

现在，{sender_name} 说了: "{message}"

请根据以上信息，以自然、拟人化的方式回复。你的回复应该：
- 简洁明了
- 符合当前对话氛围
- 体现你的个性和思考
"""
        
        # 添加记忆上下文
        if context.memory_context:
            prompt += f"\n这是关于 {sender_name} 的一些记忆，可以作为参考：\n"
            prompt += f"印象: {context.memory_context.get('impression', '无')}\n"
            prompt += f"相关记忆: {context.memory_context.get('memories', '无')}\n"
            
        return prompt
    
    def _build_simple_prompt(self, context: "ThinkingContext") -> str:
        """为普通模式构建LLM提示"""
        sender_name = context.event.get_sender_name()
        message = context.event.message_str
        
        prompt = f"""你是一个群聊机器人，正在参与一个群聊。
{sender_name} 说了: "{message}"
请以简洁、自然的方式回复。
        """
        return prompt
    
    def _post_process_reply(self, reply_content: str, context: "ThinkingContext") -> str:
        """后处理回复"""
        try:
            # 1. 长度限制
            if len(reply_content) > self.config.max_reply_length:
                reply_content = reply_content[:self.config.max_reply_length] + "..."
            
            # 2. 随机添加表情符号
            if self.config.enable_emoji and random.random() < 0.2:  # 20%概率添加表情
                emoji = random.choice(self.emojis)
                reply_content += f" {emoji}"
            
            # 3. 清理格式
            reply_content = reply_content.strip()
            
            return reply_content
            
        except Exception as e:
            logger.error(f"后处理回复失败: {e}")
            return reply_content
