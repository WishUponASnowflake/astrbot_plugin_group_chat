import time
from collections import deque
import random

class FrequencyControl:
    def __init__(self, group_id: str):
        self.group_id = group_id
        self.historical_hourly_avg_users = [0.0] * 24
        self.historical_hourly_avg_msgs = [0.0] * 24
        self.load_historical_data()

        self.recent_messages: deque[float] = deque(maxlen=100)  # 存储最近的消息时间戳
        self.focus_value = 0.0
        self.last_update_time = time.time()
        self.at_message_boost = 0.0
        self.at_message_boost_decay = 0.95
        self.smoothing_factor = 0.1  # 用于平滑焦点值变化的因子

    def load_historical_data(self):
        """加载或生成历史聊天活动数据。"""
        # 在实际应用中，这将从数据库或日志中加载数据。
        # 这里，我们生成一些模拟数据来模拟不同时间的活动。
        for hour in range(24):
            if 6 <= hour < 9:  # 早高峰
                self.historical_hourly_avg_msgs[hour] = random.uniform(30, 50)
            elif 12 <= hour < 14:  # 午间高峰
                self.historical_hourly_avg_msgs[hour] = random.uniform(40, 60)
            elif 20 <= hour < 23:  # 晚间高峰
                self.historical_hourly_avg_msgs[hour] = random.uniform(50, 80)
            else:  # 其他时间
                self.historical_hourly_avg_msgs[hour] = random.uniform(5, 15)
        print(f"为群组 {self.group_id} 加载了模拟的历史数据。")

    def update_message_rate(self, message_timestamp: float):
        """记录一条新消息并更新频率指标。"""
        self.recent_messages.append(message_timestamp)
        self._update_focus()

    def _update_focus(self):
        """根据当前聊天活动与历史基线的对比，更新焦点值。"""
        current_time = time.time()
        delta_time = current_time - self.last_update_time
        self.last_update_time = current_time

        # 计算当前小时的活动
        current_hour = time.localtime(current_time).tm_hour
        messages_in_last_minute = len([t for t in self.recent_messages if current_time - t <= 60])

        # 与历史平均值进行比较
        historical_msgs = self.historical_hourly_avg_msgs[current_hour] / 60.0  # 每分钟
        
        # 这是一个简化的调整逻辑；后续会进行改进
        target_focus = self.focus_value
        if messages_in_last_minute > historical_msgs * 1.5:
            target_focus += 0.1 * (delta_time / 60)  # 增加焦点
        else:
            target_focus -= 0.05 * (delta_time / 60)  # 减少焦点

        # 应用平滑处理
        self.focus_value += (target_focus - self.focus_value) * self.smoothing_factor

        # 应用 @ 消息的衰减增强
        self.at_message_boost *= self.at_message_boost_decay
        if self.at_message_boost < 0.01:
            self.at_message_boost = 0.0

        self.focus_value = max(0, min(1, self.focus_value)) # 将焦点值限制在 0 和 1 之间

    def boost_on_at(self):
        """当机器人被 @ 时，临时提高焦点值。"""
        self.at_message_boost = 0.5  # 设置一个初始增强值
        print(f"机器人被 @，为群组 {self.group_id} 临时提高焦点。")

    def get_focus(self) -> float:
        """获取当前的焦点值。"""
        self._update_focus()
        return self.focus_value

    def should_trigger_by_focus(self) -> bool:
        """根据焦点值决定是否触发回复。"""
        # 这是一个简化的触发器；后续会进行改进
        effective_focus = self.get_focus() + self.at_message_boost
        return effective_focus > 0.7
