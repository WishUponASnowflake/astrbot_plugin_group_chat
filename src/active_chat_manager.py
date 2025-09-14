import asyncio
import time
import re
from typing import Dict, Any

from astrbot.api import logger
from astrbot.api.event import MessageChain
from frequency_control import FrequencyControl

class GroupHeartFlow:
    HEARTBEAT_INTERVAL = 15  # 心跳检查间隔（秒）
    COOLDOWN_SECONDS = 5   # 触发冷却（秒）

    def __init__(
        self,
        group_id: str,
        context: Any,
        state_manager: Any = None,
        response_engine: Any = None,
        context_analyzer: Any = None,
        willingness_calculator: Any = None,
        plugin_config: Any = None,
    ):
        self.group_id = group_id
        self.context = context
        self.state_manager = state_manager
        self.response_engine = response_engine
        self.context_analyzer = context_analyzer
        self.willingness_calculator = willingness_calculator
        self.plugin_config = plugin_config

        self.frequency_control = FrequencyControl(group_id, state_manager, config=self.plugin_config)
        self._task = None
        self.last_trigger_ts = 0.0
        self._last_user_id = None
        self._last_message_str = ""

    async def _run_loop(self):
        """单个群组的主要主动聊天循环。"""
        while True:
            try:
                if self.frequency_control.should_trigger_by_focus():
                    now = time.time()
                    if now - self.last_trigger_ts >= self.COOLDOWN_SECONDS:
                        logger.info(f"[ActiveChat] 触发主动回复，群组 {self.group_id}")
                        await self._trigger_active_response(self.group_id)
                        self.last_trigger_ts = now
                    else:
                        logger.debug(f"[ActiveChat] 冷却中，群组 {self.group_id}")
                else:
                    logger.debug(f"[ActiveChat] 心跳 - 无动作 群组 {self.group_id}")
            except Exception as e:
                logger.error(f"[ActiveChat] 心跳循环异常 群组 {self.group_id}: {e}")
            await asyncio.sleep(self.HEARTBEAT_INTERVAL)

    def on_message(self, event: Any):
        """处理传入的消息以更新频率控制。"""
        user_id = event.get_sender_id()
        self._last_user_id = user_id
        self._last_message_str = getattr(event, "message_str", "") or ""
        self.frequency_control.update_message_rate(time.time(), user_id)

        # 智能检查是否 @ 了机器人
        if self._is_bot_mentioned(event):
            self.frequency_control.boost_on_at()

    def _is_bot_mentioned(self, event: Any) -> bool:
        """智能检测机器人是否被提及（基于人格动态关键词）"""
        message_str = event.message_str

        # 方法1：检查AstrBot的事件属性（最可靠）
        if hasattr(event, 'is_at_or_wake_command') and event.is_at_or_wake_command:
            return True

        # 方法2：检查消息中是否包含@符号
        if "@" not in message_str:
            return False

        # 方法3：从人格系统中获取动态关键词
        dynamic_keywords = self._get_persona_based_keywords()

        # 方法4：智能@检测
        # 从消息中提取可能的@提及
        import re
        at_mentions = re.findall(r'@(\w+)', message_str)

        if not at_mentions:
            return False

        # 检查@的用户名是否包含机器人相关关键词
        for mention in at_mentions:
            mention_lower = mention.lower()
            if any(keyword in mention_lower for keyword in dynamic_keywords):
                return True

        # 方法5：检查消息内容是否包含机器人相关语境
        context_indicators = self._get_persona_based_contexts()

        message_lower = message_str.lower()
        has_context = any(indicator in message_lower for indicator in context_indicators)

        # 如果既有@又有多于2个提及，可能是@机器人
        if len(at_mentions) >= 2 and has_context:
            return True

        # 方法6：检查消息是否以@开头（直接@机器人）
        if message_str.strip().startswith('@'):
            return True

        return False

    def _get_persona_based_keywords(self) -> list:
        """从人格系统中获取动态关键词"""
        try:
            # 尝试从AstrBot的人格系统中获取关键词
            if hasattr(self.context, 'provider_manager') and self.context.provider_manager:
                personas = getattr(self.context.provider_manager, 'personas', {})
                selected_persona = getattr(self.context.provider_manager, 'selected_default_persona', {})

                # 获取当前使用的人格
                current_persona_name = selected_persona.get('name', '')
                if current_persona_name and current_persona_name in personas:
                    persona_data = personas[current_persona_name]
                    # 从人格描述中提取关键词
                    persona_keywords = self._extract_keywords_from_persona(persona_data)
                    if persona_keywords:
                        return persona_keywords

            # 从配置中获取自定义关键词
            config_keywords = getattr(self.context, 'config', {}).get('bot_keywords', [])
            if config_keywords:
                return config_keywords

        except Exception as e:
            print(f"获取人格关键词失败: {e}")

        # 默认关键词（兜底方案）
        return [
            '机器人', 'bot', '助手', 'ai', '智能',
            '小助手', '机器人君', 'ai助手'
        ]

    def _extract_keywords_from_persona(self, persona_data: dict) -> list:
        """从人格数据中提取关键词"""
        keywords = []

        try:
            # 从人格名称中提取
            if 'name' in persona_data:
                name = persona_data['name']
                # 分割名称为关键词
                name_parts = re.split(r'[_\-\s]', name)
                keywords.extend([part.lower() for part in name_parts if len(part) > 1])

            # 从人格描述中提取关键词
            if 'description' in persona_data:
                description = persona_data['description']
                # 提取描述中的关键词（简单分词）
                desc_words = re.findall(r'[\u4e00-\u9fa5a-zA-Z]+', description)
                # 过滤出可能的机器人相关词
                for word in desc_words:
                    word_lower = word.lower()
                    if len(word_lower) >= 2 and any(char.isalpha() for char in word_lower):
                        keywords.append(word_lower)

            # 从人格提示词中提取
            if 'prompt' in persona_data:
                prompt = persona_data['prompt']
                prompt_words = re.findall(r'[\u4e00-\u9fa5a-zA-Z]+', prompt)
                keywords.extend([word.lower() for word in prompt_words if len(word) >= 2])

        except Exception as e:
            print(f"提取人格关键词失败: {e}")

        # 去重并返回
        return list(set(keywords)) if keywords else []

    def _get_persona_based_contexts(self) -> list:
        """从人格系统中获取动态语境词"""
        try:
            # 从配置中获取自定义语境词
            config_contexts = getattr(self.context, 'config', {}).get('bot_contexts', [])
            if config_contexts:
                return config_contexts

        except Exception as e:
            print(f"获取人格语境词失败: {e}")

        # 默认语境词
        return [
            '在吗', '在不在', '来一下', '帮帮忙', '回答一下',
            '说句话', '回个话', '出来', '出来聊聊'
        ]

    def start(self):
        """为群组启动心跳循环。"""
        if self._task is None:
            self._task = asyncio.create_task(self._run_loop())
            print(f"已为群组 {self.group_id} 启动心跳")

    def stop(self):
        """为群组停止心跳循环。"""
        if self._task:
            self._task.cancel()
            self._task = None
            print(f"已为群组 {self.group_id} 停止心跳")

    async def _trigger_active_response(self, group_id: str):
        """触发主动回复流程"""
        try:
            umo = self.state_manager.get_group_umo(group_id) if self.state_manager else None
            if not umo:
                logger.debug(f"[ActiveChat] 群组 {group_id} 未记录 UMO，跳过主动发送")
                return

            if not (self.response_engine and self.context_analyzer and self.willingness_calculator):
                logger.debug(f"[ActiveChat] 依赖未就绪，跳过主动发送 群组 {group_id}")
                return

            event = self._create_virtual_event(group_id, umo)
            chat_context = await self.context_analyzer.analyze_chat_context(event)
            willingness_result = await self.willingness_calculator.calculate_response_willingness(event, chat_context)
            response_result = await self.response_engine.generate_response(event, chat_context, willingness_result)

            if response_result.get("should_reply"):
                content = (response_result.get("content") or "").strip()
                if content:
                    await self._send_active_message(umo, content)
                    logger.info(f"[ActiveChat] 群组 {group_id} 主动发送成功")
                else:
                    logger.debug(f"[ActiveChat] LLM 决定回复但内容为空，跳过 群组 {group_id}")
            else:
                logger.debug(f"[ActiveChat] LLM 决定不回复 群组 {group_id}")
        except Exception as e:
            logger.error(f"[ActiveChat] 主动回复异常 群组 {group_id}: {e}")

    def _create_virtual_event(self, group_id: str, umo: str):
        """构建用于主动流程的虚拟事件"""
        last_uid = self._last_user_id or "virtual_user"
        msg = self._last_message_str or "冒个泡～"
        class VirtualEvent:
            def __init__(self, gid, uid, msg, umo):
                self._gid = gid
                self._uid = uid
                self.message_str = msg
                self.unified_msg_origin = umo
                self.is_at_or_wake_command = False
            def get_group_id(self):
                return self._gid
            def get_sender_id(self):
                return self._uid
        return VirtualEvent(group_id, last_uid, msg, umo)

    async def _send_active_message(self, umo: str, content: str):
        """向指定会话发送主动消息"""
        try:
            chain = MessageChain().message(content)
            await self.context.send_message(umo, chain)
        except Exception as e:
            logger.error(f"[ActiveChat] 发送主动消息失败: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """获取当前群组主动模块的状态"""
        now = time.time()
        cooldown_remaining = max(0.0, self.COOLDOWN_SECONDS - (now - self.last_trigger_ts)) if self.last_trigger_ts else 0.0
        focus = self.frequency_control.get_focus()
        at_boost = self.frequency_control.at_message_boost
        effective = focus + at_boost
        threshold = getattr(self.frequency_control, "threshold", 0.55)
        messages_last_minute = self.frequency_control.get_messages_in_last_minute() if hasattr(self.frequency_control, "get_messages_in_last_minute") else 0
        has_umo = self.state_manager.get_group_umo(self.group_id) is not None if self.state_manager else False
        return {
            "group_id": self.group_id,
            "has_umo": has_umo,
            "last_trigger_ts": self.last_trigger_ts,
            "cooldown_remaining": cooldown_remaining,
            "focus": focus,
            "at_boost": at_boost,
            "effective": effective,
            "threshold": threshold,
            "messages_last_minute": messages_last_minute,
        }

class ActiveChatManager:
    def __init__(self, context: Any, state_manager: Any = None, response_engine: Any = None, context_analyzer: Any = None, willingness_calculator: Any = None, plugin_config: Any = None):
        self.context = context
        self.state_manager = state_manager
        self.response_engine = response_engine
        self.context_analyzer = context_analyzer
        self.willingness_calculator = willingness_calculator
        self.plugin_config = plugin_config
        self.group_flows: Dict[str, GroupHeartFlow] = {}

    def start_all_flows(self):
        """为所有配置的群组启动主动聊天监控。"""
        # 从状态管理器获取活跃群组列表
        if self.state_manager:
            active_groups = self.state_manager.get("active_groups", [])
            # 如果没有活跃群组，从配置中获取默认群组
            if not active_groups:
                # 从配置获取群组列表（如果有的话）
                config_groups = getattr(self.context, 'config', {}).get('active_groups', [])
                if config_groups:
                    active_groups = config_groups
                else:
                    # 智能检测：从最近的聊天记录中提取活跃群组
                    active_groups = self._detect_active_groups_from_history()
        else:
            # 回退方案：智能检测活跃群组
            active_groups = self._detect_active_groups_from_history()

        logger.info(f"检测到 {len(active_groups)} 个活跃群组: {active_groups}")

        for group_id in active_groups:
            if group_id not in self.group_flows:
                flow = GroupHeartFlow(
                    group_id,
                    self.context,
                    self.state_manager,
                    response_engine=self.response_engine,
                    context_analyzer=self.context_analyzer,
                    willingness_calculator=self.willingness_calculator,
                    plugin_config=self.plugin_config
                )
                self.group_flows[group_id] = flow
                flow.start()

    def ensure_flow(self, group_id: str):
        """确保指定群组存在心跳流程"""
        if group_id not in self.group_flows:
            flow = GroupHeartFlow(
                group_id,
                self.context,
                self.state_manager,
                response_engine=self.response_engine,
                context_analyzer=self.context_analyzer,
                willingness_calculator=self.willingness_calculator,
                plugin_config=self.plugin_config
            )
            self.group_flows[group_id] = flow
            flow.start()

    async def trigger_now(self, group_id: str):
        """立刻对指定群执行一次主动回复（绕过阈值与冷却）"""
        self.ensure_flow(group_id)
        flow = self.group_flows[group_id]
        await flow._trigger_active_response(group_id)
        flow.last_trigger_ts = time.time()

    def get_stats(self, group_id: str) -> Dict[str, Any]:
        """获取指定群当前的主动模块状态"""
        flow = self.group_flows.get(group_id)
        if not flow:
            return {
                "group_id": group_id,
                "has_flow": False
            }
        stats = flow.get_stats()
        stats["has_flow"] = True
        return stats

    def set_threshold(self, group_id: str, value: float) -> bool:
        """设置指定群的触发阈值"""
        flow = self.group_flows.get(group_id)
        if not flow:
            return False
        if hasattr(flow.frequency_control, "set_threshold"):
            flow.frequency_control.set_threshold(value)
            return True
        return False

    def _detect_active_groups_from_history(self) -> list:
        """从聊天历史中智能检测活跃群组。"""
        active_groups = set()

        # 如果有状态管理器，从中获取历史数据
        if self.state_manager:
            # 从各种历史数据中提取群组ID
            conversation_counts = self.state_manager.get_conversation_counts()
            active_groups.update(conversation_counts.keys())

            # 从疲劳数据中提取
            fatigue_data = self.state_manager.get_fatigue_data()
            for key in fatigue_data.keys():
                if '_' in key:
                    group_id = key.split('_')[0]
                    active_groups.add(group_id)

        # 如果没有找到活跃群组，提供一些默认的检测逻辑
        if not active_groups:
            # 这里可以实现更复杂的检测逻辑，比如：
            # 1. 从机器人平台API获取当前加入的群组
            # 2. 从配置文件读取
            # 3. 使用机器学习模型预测可能活跃的群组
            print("未检测到活跃群组，使用默认列表")
            active_groups = ["default_group_1", "default_group_2"]

        return list(active_groups)

    def stop_all_flows(self):
        """停止所有主动聊天监控循环。"""
        for flow in self.group_flows.values():
            flow.stop()
        self.group_flows.clear()

    def update_group_list(self, group_ids: list[str]):
        """更新被监控的群组列表。"""
        # 停止不再在列表中的群组的流
        for group_id in list(self.group_flows.keys()):
            if group_id not in group_ids:
                self.group_flows[group_id].stop()
                del self.group_flows[group_id]

        # 为新群组启动流
        for group_id in group_ids:
            if group_id not in self.group_flows:
                flow = GroupHeartFlow(
                    group_id,
                    self.context,
                    self.state_manager,
                    response_engine=self.response_engine,
                    context_analyzer=self.context_analyzer,
                    willingness_calculator=self.willingness_calculator,
                    plugin_config=self.plugin_config
                )
                self.group_flows[group_id] = flow
                flow.start()
