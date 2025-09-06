import asyncio
import time
from typing import Dict, Any

from frequency_control import FrequencyControl

class GroupHeartFlow:
    def __init__(self, group_id: str, context: Any):
        self.group_id = group_id
        self.context = context
        self.frequency_control = FrequencyControl(group_id)
        self._task = None

    async def _run_loop(self):
        """单个群组的主要主动聊天循环。"""
        while True:
            if self.frequency_control.should_trigger_by_focus():
                print(f"焦点触发器激活，为群组 {self.group_id} 发送消息。")
                # 在这里，我们将调用实际的响应生成逻辑
                # self.context.send_message(...)
            else:
                print(f"群组 {self.group_id} 的心跳 - 无动作")
            
            await asyncio.sleep(15)  # 检查频率

    def on_message(self, event: Any):
        """处理传入的消息以更新频率控制。"""
        self.frequency_control.update_message_rate(time.time())

        # 检查是否 @ 了机器人
        # 注意：这是一种简化的检查方式。在实际应用中，需要更可靠的方法来获取机器人的 ID。
        bot_id = "your_bot_id" # 占位符
        if f"@{bot_id}" in event.get_message_str():
            self.frequency_control.boost_on_at()

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

class ActiveChatManager:
    def __init__(self, context: Any):
        self.context = context
        self.group_flows: Dict[str, GroupHeartFlow] = {}

    def start_all_flows(self):
        """为所有配置的群组启动主动聊天监控。"""
        # 在实际实现中，您将从机器人的配置或当前状态中获取群组列表。
        # 目前，我们使用一个占位符。
        group_ids = ["group_1", "group_2"] # 占位符
        for group_id in group_ids:
            if group_id not in self.group_flows:
                flow = GroupHeartFlow(group_id, self.context)
                self.group_flows[group_id] = flow
                flow.start()

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
                flow = GroupHeartFlow(group_id, self.context)
                self.group_flows[group_id] = flow
                flow.start()
