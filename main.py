from typing import Dict, List, Optional, Any, AsyncGenerator
import sys
import os
from pathlib import Path

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger

# 添加src目录到Python路径
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

# 导入自定义模块
from active_chat_manager import ActiveChatManager
from group_list_manager import GroupListManager
from impression_manager import ImpressionManager
from memory_integration import MemoryIntegration
from interaction_manager import InteractionManager
from response_engine import ResponseEngine
from willingness_calculator import WillingnessCalculator
from focus_chat_manager import FocusChatManager
from fatigue_system import FatigueSystem
from context_analyzer import ContextAnalyzer
from state_manager import StateManager

@register("astrbot_plugin_group_chat", "qa296", "一个高级群聊交互插件，能像真人一样主动参与对话，实现拟人化的主动交互体验", "1.0.0", "https://github.com/qa296/astrbot_plugin_group_chat")
class GroupChatPlugin(Star):
    def __init__(self, context: Context, config: Any):
        super().__init__(context)
        self.config = config
        
        # 初始化状态管理器（符合文档要求的持久化存储）
        self.state_manager = StateManager(context, config)
        
        # 初始化主动聊天管理器
        self.active_chat_manager = ActiveChatManager(context)
        
        # 初始化组件
        self.group_list_manager = GroupListManager(config)
        self.impression_manager = ImpressionManager(context, config)
        self.memory_integration = MemoryIntegration(context, config)
        self.interaction_manager = InteractionManager(context, config, self.state_manager)
        self.response_engine = ResponseEngine(context, config)
        self.willingness_calculator = WillingnessCalculator(context, config, self.impression_manager, self.state_manager)
        self.focus_chat_manager = FocusChatManager(context, config, self.state_manager)
        self.fatigue_system = FatigueSystem(config, self.state_manager)
        self.context_analyzer = ContextAnalyzer(context, config, self.state_manager, self.impression_manager, self.memory_integration)
        
        logger.info("群聊插件初始化完成")

    @filter.on_astrbot_loaded()
    async def on_astrbot_loaded(self):
        """AstrBot 初始化完成后启动主动聊天管理器。"""
        logger.info("AstrBot 已加载，正在启动 ActiveChatManager...")
        self.active_chat_manager.start_all_flows()
    
    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    async def on_group_message(self, event: AstrMessageEvent):
        """处理群聊消息的主入口"""
        group_id = event.get_group_id()
        
        # 将消息传递给 ActiveChatManager 以进行频率分析
        if group_id in self.active_chat_manager.group_flows:
            self.active_chat_manager.group_flows[group_id].on_message(event)

        # 1. 群组权限检查
        if not self.group_list_manager.check_group_permission(group_id):
            return
        
        # 2. 处理消息
        async for result in self._process_group_message(event):
            yield result
    
    async def _process_group_message(self, event: AstrMessageEvent):
        """处理群聊消息的核心逻辑"""
        group_id = event.get_group_id()
        user_id = event.get_sender_id()
        
        # 获取聊天上下文
        chat_context = await self.context_analyzer.analyze_chat_context(event)
        
        # 判断交互模式
        interaction_mode = self.interaction_manager.determine_interaction_mode(chat_context)
        
        # 观察模式不回复
        if interaction_mode == "observation":
            return
        
        # 计算回复意愿
        willingness_result = await self.willingness_calculator.calculate_response_willingness(event, chat_context)
        
        # 如果不需要 LLM 决策且意愿不足，直接跳过
        if not willingness_result.get("requires_llm_decision") and not willingness_result.get("should_respond"):
            return
        
        # 检查连续回复限制
        max_consecutive = getattr(self.config, 'max_consecutive_responses', 3)
        consecutive_count = self.state_manager.get_consecutive_responses().get(group_id, 0)
        if consecutive_count >= max_consecutive:
            return
        
        # 生成回复（包含读空气功能）
        response_result = await self.response_engine.generate_response(event, chat_context, willingness_result)
        
        # 根据结果决定是否回复
        if response_result.get("should_reply"):
            response_content = response_result.get("content")
            if response_content:
                yield event.plain_result(response_content)
                
                # 更新连续回复计数
                self.state_manager.increment_consecutive_response(group_id)
                
                # 记录决策信息（用于调试）
                decision_method = response_result.get("decision_method")
                willingness_score = response_result.get("willingness_score")
                logger.debug(f"群组 {group_id} 回复 - 方法: {decision_method}, 意愿分: {willingness_score:.2f}")
        else:
            # 记录跳过回复的原因
            decision_method = response_result.get("decision_method")
            skip_reason = response_result.get("skip_reason", "意愿不足")
            willingness_score = response_result.get("willingness_score")
            logger.debug(f"群组 {group_id} 跳过回复 - 方法: {decision_method}, 原因: {skip_reason}, 意愿分: {willingness_score:.2f}")
        
        # 更新交互状态
        await self.interaction_manager.update_interaction_state(event, chat_context, response_result)
    
    async def terminate(self):
        """插件终止时的清理工作"""
        logger.info("群聊插件正在终止...")
        # 停止主动聊天管理器
        self.active_chat_manager.stop_all_flows()
        # 使用状态管理器清理所有持久化状态
        self.state_manager.clear_all_state()
        logger.info("群聊插件已终止")
