"""
AstrBot Group Chat Plugin - Chat Manager
聊天管理器模块，处理消息评估和回复生成
"""

import asyncio
import time
import random
from typing import Dict, List, Optional, Any, Tuple

from astrbot.api.event import AstrMessageEvent, MessageEventResult
from astrbot.api import logger
from astrbot.api.message_components import Plain

from .interest_evaluator import InterestEvaluator
from .reply_generator import ReplyGenerator
from .fatigue_manager import FatigueManager
from .memory_integration import MemoryIntegration
from .types import ChatMode, WillingnessMode, UserState, GroupState, ThinkingContext


class GroupChatManager:
    """群聊管理器"""
    
    def __init__(self, context, plugin_config):
        self.context = context
        self.config = plugin_config
        
        # 初始化子模块
        self.interest_evaluator = InterestEvaluator(plugin_config)
        self.reply_generator = ReplyGenerator(plugin_config, self.context)
        self.fatigue_manager = FatigueManager(plugin_config)
        self.memory_integration = MemoryIntegration(plugin_config, context)
        
        # 状态管理
        self.user_states: Dict[str, UserState] = {}  # user_id:group_id -> UserState
        self.group_states: Dict[str, GroupState] = {}  # group_id -> GroupState
        
        # 统计信息
        self.total_messages_processed = 0
        self.total_replies_sent = 0
        
        logger.info("GroupChatManager 初始化完成")
    
    def _get_user_state_key(self, user_id: str, group_id: str) -> str:
        """获取用户状态键"""
        return f"{user_id}:{group_id}"
    
    def _get_or_create_user_state(self, user_id: str, group_id: str) -> UserState:
        """获取或创建用户状态"""
        key = self._get_user_state_key(user_id, group_id)
        if key not in self.user_states:
            self.user_states[key] = UserState(
                user_id=user_id,
                group_id=group_id,
                willingness=self.config.classic_base_willingness
            )
        return self.user_states[key]
    
    def _get_or_create_group_state(self, group_id: str) -> GroupState:
        """获取或创建群组状态"""
        if group_id not in self.group_states:
            self.group_states[group_id] = GroupState(group_id=group_id)
        return self.group_states[group_id]
    
    async def process_message(self, event: AstrMessageEvent) -> Optional[MessageEventResult]:
        """处理消息的主入口"""
        try:
            # 更新统计
            self.total_messages_processed += 1
            
            # 获取基本信息
            user_id = event.get_sender_id()
            group_id = event.get_group_id()
            message_content = event.message_str
            
            if not group_id:  # 不是群聊消息
                return None
            
            # 获取或创建状态
            user_state = self._get_or_create_user_state(user_id, group_id)
            group_state = self._get_or_create_group_state(group_id)
            
            # 更新群组状态
            await self._update_group_state(group_state, user_id, message_content)
            
            # 评估兴趣度
            interest_score = await self.interest_evaluator.evaluate_interest(event, user_state, group_state)
            
            # 构建思考上下文
            thinking_context = await self._build_thinking_context(
                event, user_state, group_state, interest_score
            )
            
            # 决定是否进入专注聊天模式
            if (self.config.enable_focused_chat and 
                interest_score >= self.config.focused_chat_threshold and
                self._can_switch_to_focused_mode(group_state)):
                
                return await self._handle_focused_chat(thinking_context)
            else:
                return await self._handle_normal_chat(thinking_context)
                
        except Exception as e:
            logger.error(f"处理消息时发生错误: {e}")
            return None
    
    async def _update_group_state(self, group_state: GroupState, user_id: str, message_content: str):
        """更新群组状态"""
        current_time = time.time()
        
        # 更新最后消息时间
        group_state.last_message_time = current_time
        
        # 更新消息计数
        group_state.message_count += 1
        
        # 更新活跃用户
        if user_id not in group_state.active_users:
            group_state.active_users.append(user_id)
        
        # 计算群聊热度（基于消息频率）
        time_diff = current_time - group_state.last_message_time
        if time_diff > 0:
            heat_increment = min(1.0 / time_diff, 0.1)  # 消息越频繁，热度增加越快
            group_state.chat_heat = min(group_state.chat_heat + heat_increment, 1.0)
        else:
            group_state.chat_heat = max(group_state.chat_heat - 0.01, 0.0)  # 缓慢衰减
    
    def _can_switch_to_focused_mode(self, group_state: GroupState) -> bool:
        """检查是否可以切换到专注模式"""
        current_time = time.time()
        cooldown_passed = (current_time - group_state.mode_switch_time) >= self.config.mode_switch_cooldown
        return cooldown_passed
    
    async def _build_thinking_context(self, event: AstrMessageEvent, user_state: UserState, 
                                   group_state: GroupState, interest_score: float) -> ThinkingContext:
        """构建思考上下文"""
        thinking_context = ThinkingContext(
            event=event,
            user_state=user_state,
            group_state=group_state,
            interest_score=interest_score
        )
        
        # 集成记忆上下文（如果启用）
        if self.config.enable_memory_integration:
            memory_context = await self.memory_integration.get_memory_context(event, user_state, group_state)
            thinking_context.memory_context = memory_context
        
        # 构建思考材料
        thinking_context.thinking_material = await self._build_thinking_material(thinking_context)
        
        return thinking_context
    
    async def _build_thinking_material(self, context: ThinkingContext) -> Dict[str, Any]:
        """构建思考材料"""
        material = {
            "message_content": context.event.message_str,
            "sender_name": context.event.get_sender_name(),
            "interest_score": context.interest_score,
            "user_willingness": context.user_state.willingness,
            "group_chat_heat": context.group_state.chat_heat,
            "current_mode": context.group_state.current_mode.value,
            "timestamp": time.time()
        }
        
        # 添加记忆信息
        if context.memory_context:
            material["memory_context"] = context.memory_context
        
        # 添加上下文信息
        material["conversation_streak"] = context.user_state.conversation_streak
        material["fatigue_level"] = context.user_state.fatigue_level
        
        return material
    
    async def _handle_focused_chat(self, context: ThinkingContext) -> Optional[MessageEventResult]:
        """处理专注聊天模式"""
        logger.info(f"进入专注聊天模式，兴趣度: {context.interest_score:.2f}")
        
        # 切换模式
        context.group_state.current_mode = ChatMode.FOCUSED
        context.group_state.mode_switch_time = time.time()
        
        # 执行专注思考循环
        return await self._focused_thinking_loop(context)
    
    async def _focused_thinking_loop(self, context: ThinkingContext) -> Optional[MessageEventResult]:
        """专注思考循环：观察-处理-规划-行动"""
        try:
            # 1. 观察（Observation）- 已经在构建思考上下文时完成
            
            # 2. 处理（Processing）- 并行处理各种信息
            processing_result = await self._parallel_processing(context)
            
            # 3. 规划（Planning）- 决定行动方案
            action_plan = await self._planning_stage(context, processing_result)
            
            # 4. 行动（Action）- 执行行动
            return await self._action_stage(context, action_plan)
            
        except Exception as e:
            logger.error(f"专注思考循环发生错误: {e}")
            return None
    
    async def _parallel_processing(self, context: ThinkingContext) -> Dict[str, Any]:
        """并行处理阶段"""
        # 创建并行任务
        tasks = [
            self._process_working_memory(context),
            self._process_relationship_context(context),
            self._process_tool_context(context),
            self._process_expression_style(context)
        ]
        
        # 等待所有任务完成
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 整合结果
        processing_result = {
            "working_memory": results[0] if not isinstance(results[0], Exception) else {},
            "relationship": results[1] if not isinstance(results[1], Exception) else {},
            "tools": results[2] if not isinstance(results[2], Exception) else {},
            "expression_style": results[3] if not isinstance(results[3], Exception) else {}
        }
        
        return processing_result
    
    async def _process_working_memory(self, context: ThinkingContext) -> Dict[str, Any]:
        """处理工作记忆"""
        return {
            "current_message": context.event.message_str,
            "recent_interactions": self._get_recent_interactions(context.user_state),
            "conversation_context": self._get_conversation_context(context.group_state)
        }
    
    async def _process_relationship_context(self, context: ThinkingContext) -> Dict[str, Any]:
        """处理关系上下文"""
        return {
            "sender_id": context.user_state.user_id,
            "personal_interest": context.user_state.personal_interest,
            "conversation_streak": context.user_state.conversation_streak,
            "memory_impression": context.memory_context.get("impression", {}) if context.memory_context else {}
        }
    
    async def _process_tool_context(self, context: ThinkingContext) -> Dict[str, Any]:
        """处理工具上下文"""
        return {
            "available_tools": ["reply_generator", "memory_integration"],
            "tool_status": "ready"
        }
    
    async def _process_expression_style(self, context: ThinkingContext) -> Dict[str, Any]:
        """处理表达风格"""
        return {
            "style": "natural",
            "emoji_enabled": self.config.enable_emoji,
            "max_length": self.config.max_reply_length
        }
    
    async def _planning_stage(self, context: ThinkingContext, processing_result: Dict[str, Any]) -> Dict[str, Any]:
        """规划阶段"""
        # 检查疲劳状态
        if self.fatigue_manager.is_fatigued(context.user_state):
            return {
                "action": "rest",
                "reason": "fatigue",
                "parameters": {}
            }
        
        # 计算回复意愿
        willingness = await self._calculate_focused_willingness(context, processing_result)
        
        if willingness < 0.3:  # 意愿过低，不回复
            return {
                "action": "ignore",
                "reason": "low_willingness",
                "parameters": {}
            }
        
        # 决定回复方式
        reply_mode = self.config.reply_mode
        
        return {
            "action": "reply",
            "reason": "normal_response",
            "parameters": {
                "reply_mode": reply_mode,
                "willingness": willingness,
                "processing_result": processing_result
            }
        }
    
    async def _calculate_focused_willingness(self, context: ThinkingContext, processing_result: Dict[str, Any]) -> float:
        """计算专注模式的回复意愿"""
        config = self.config.get_mode_config("focused")
        
        # 基础意愿
        willingness = config["base_willingness"]
        
        # 个人化因素
        personal_factor = processing_result["relationship"].get("personal_interest", 0.5)
        willingness += personal_factor * config["personal_factor"]
        
        # 群聊热度因素
        chat_heat = context.group_state.chat_heat
        willingness += chat_heat * config["chat_heat_factor"]
        
        # 连续对话因素
        conversation_streak = context.user_state.conversation_streak
        willingness += min(conversation_streak * 0.1, 0.5) * config["conversation_factor"]
        
        # 说话频率因素
        frequency_factor = self._calculate_frequency_factor(context.user_state)
        willingness += frequency_factor * config["frequency_factor"]
        
        # 疲劳因素
        fatigue_factor = 1.0 - context.user_state.fatigue_level
        willingness *= fatigue_factor
        
        # 记忆影响（如果启用）
        if context.memory_context:
            memory_influence = context.memory_context.get("influence", 0.0)
            willingness += memory_influence * self.config.memory_influence_weight
        
        return min(max(willingness, 0.0), 1.0)
    
    def _calculate_frequency_factor(self, user_state: UserState) -> float:
        """计算说话频率因素"""
        current_time = time.time()
        time_since_last_reply = current_time - user_state.last_interaction_time
        
        if time_since_last_reply < 60:  # 1分钟内回复过
            return -0.3  # 降低意愿
        elif time_since_last_reply < 300:  # 5分钟内回复过
            return 0.0  # 正常
        else:  # 很久没回复
            return 0.2  # 提高意愿
    
    async def _action_stage(self, context: ThinkingContext, action_plan: Dict[str, Any]) -> Optional[MessageEventResult]:
        """行动阶段"""
        action = action_plan["action"]
        
        if action == "rest":
            logger.info("因疲劳选择休息")
            return None
        elif action == "ignore":
            logger.info("意愿过低，选择忽略")
            return None
        elif action == "reply":
            return await self._execute_reply(context, action_plan["parameters"])
        else:
            logger.warning(f"未知的行动类型: {action}")
            return None
    
    async def _execute_reply(self, context: ThinkingContext, parameters: Dict[str, Any]) -> MessageEventResult:
        """执行回复"""
        try:
            # 生成回复
            reply_content = await self.reply_generator.generate_reply(
                context, parameters["reply_mode"], parameters["processing_result"]
            )
            
            if not reply_content:
                return None
            
            # 模拟打字延迟
            if self.config.typing_simulation_enabled:
                await self._simulate_typing()
            
            # 更新用户状态
            await self._update_user_state_after_reply(context.user_state)
            
            # 更新统计
            self.total_replies_sent += 1
            
            # 添加记忆（如果启用）
            if self.config.enable_memory_integration:
                await self.memory_integration.add_interaction_memory(context, reply_content)
            
            return context.event.plain_result(reply_content)
            
        except Exception as e:
            logger.error(f"执行回复时发生错误: {e}")
            return None
    
    async def _simulate_typing(self):
        """模拟打字延迟"""
        delay = random.uniform(self.config.typing_min_delay, self.config.typing_max_delay)
        await asyncio.sleep(delay)
    
    async def _update_user_state_after_reply(self, user_state: UserState):
        """回复后更新用户状态"""
        current_time = time.time()
        
        # 更新最后交互时间
        user_state.last_interaction_time = current_time
        
        # 更新回复次数
        user_state.reply_count += 1
        user_state.consecutive_replies += 1
        
        # 更新疲劳程度
        user_state.fatigue_level = self.fatigue_manager.update_fatigue(user_state)
        
        # 更新连续对话计数
        user_state.conversation_streak += 1
    
    async def _handle_normal_chat(self, context: ThinkingContext) -> Optional[MessageEventResult]:
        """处理普通聊天模式"""
        logger.debug("处理普通聊天模式")
        
        # 计算回复意愿
        willingness = await self._calculate_normal_willingness(context)
        
        # 应用概率倍数
        willingness *= self.config.response_probability_multiplier
        
        if random.random() > willingness:
            return None
        
        # 生成回复
        reply_content = await self.reply_generator.generate_simple_reply(context)
        
        if reply_content:
            # 更新状态
            await self._update_user_state_after_reply(context.user_state)
            self.total_replies_sent += 1
            
            return context.event.plain_result(reply_content)
        
        return None
    
    async def _calculate_normal_willingness(self, context: ThinkingContext) -> float:
        """计算普通模式的回复意愿"""
        config = self.config.get_mode_config("classic")
        
        # 基础意愿
        willingness = config["base_willingness"]
        
        # 被@时的提升
        if context.event.is_at_or_wake_command:
            willingness += config["at_boost"]
        
        # 兴趣度影响
        willingness += context.interest_score * config["topic_interest_boost"]
        
        # 时间衰减
        time_since_last_reply = time.time() - context.user_state.last_interaction_time
        time_decay = config["time_decay_rate"] ** (time_since_last_reply / 60)  # 每分钟衰减
        willingness *= time_decay
        
        # 疲劳影响
        fatigue_factor = 1.0 - context.user_state.fatigue_level
        willingness *= fatigue_factor
        
        return min(max(willingness, 0.0), 1.0)
    
    def _get_recent_interactions(self, user_state: UserState) -> List[Dict[str, Any]]:
        """获取最近的交互记录"""
        # 这里可以实现更复杂的交互记录管理
        return []
    
    def _get_conversation_context(self, group_state: GroupState) -> Dict[str, Any]:
        """获取对话上下文"""
        return {
            "group_id": group_state.group_id,
            "chat_heat": group_state.chat_heat,
            "active_users": len(group_state.active_users),
            "current_mode": group_state.current_mode.value
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_messages_processed": self.total_messages_processed,
            "total_replies_sent": self.total_replies_sent,
            "active_users": len(self.user_states),
            "active_groups": len(self.group_states),
            "reply_rate": self.total_replies_sent / max(self.total_messages_processed, 1)
        }
