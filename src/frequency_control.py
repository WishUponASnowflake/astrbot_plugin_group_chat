import time
from collections import deque
import random
from typing import Dict, List, Any, Optional
from pathlib import Path
import json

class FrequencyControl:
    def __init__(self, group_id: str, state_manager: Optional[Any] = None):
        self.group_id = group_id
        self.state_manager = state_manager
        self.historical_hourly_avg_users = [0.0] * 24
        self.historical_hourly_avg_msgs = [0.0] * 24

        # 历史数据存储
        self.hourly_message_counts = {hour: [] for hour in range(24)}  # 每个小时的消息计数历史
        self.hourly_user_counts = {hour: [] for hour in range(24)}    # 每个小时的用户计数历史
        self.daily_stats = {}  # 按日期存储的统计数据

        self.load_historical_data()

        self.recent_messages: deque[float] = deque(maxlen=100)  # 存储最近的消息时间戳
        self.recent_users: set = set()  # 最近活跃的用户
        self.focus_value = 0.0
        self.last_update_time = time.time()
        self.at_message_boost = 0.0
        self.at_message_boost_decay = 0.95
        self.smoothing_factor = 0.1  # 用于平滑焦点值变化的因子

    def load_historical_data(self):
        """从历史数据加载或生成基础数据。"""
        if self.state_manager:
            # 尝试从状态管理器加载历史数据
            historical_data = self.state_manager.get(f"frequency_data_{self.group_id}", {})

            if historical_data and 'hourly_message_counts' in historical_data:
                # 从数据加载
                self.hourly_message_counts = historical_data.get('hourly_message_counts', self.hourly_message_counts)
                self.hourly_user_counts = historical_data.get('hourly_user_counts', self.hourly_user_counts)
                self.daily_stats = historical_data.get('daily_stats', {})

                # 计算历史平均值
                self._calculate_historical_averages()
                print(f"为群组 {self.group_id} 加载了的历史数据。")
                return

        # 如果没有历史数据，使用智能默认值（基于群组类型和时间模式）
        self._generate_smart_defaults()
        print(f"为群组 {self.group_id} 生成了智能默认的历史数据。")

    def _calculate_historical_averages(self):
        """根据收集的历史数据计算平均值。"""
        for hour in range(24):
            msg_counts = self.hourly_message_counts.get(hour, [])
            user_counts = self.hourly_user_counts.get(hour, [])

            if msg_counts:
                # 计算消息数的平均值
                self.historical_hourly_avg_msgs[hour] = sum(msg_counts) / len(msg_counts)
            else:
                # 如果没有数据，使用智能默认值
                self.historical_hourly_avg_msgs[hour] = self._get_smart_default_msgs(hour)

            if user_counts:
                # 计算用户数的平均值
                self.historical_hourly_avg_users[hour] = sum(user_counts) / len(user_counts)
            else:
                # 如果没有数据，使用智能默认值
                self.historical_hourly_avg_users[hour] = self._get_smart_default_users(hour)

    def _generate_smart_defaults(self):
        """生成基于时间模式的智能默认值。"""
        for hour in range(24):
            self.historical_hourly_avg_msgs[hour] = self._get_smart_default_msgs(hour)
            self.historical_hourly_avg_users[hour] = self._get_smart_default_users(hour)

    def _get_smart_default_msgs(self, hour: int) -> float:
        """根据小时获取智能默认消息数。"""
        # 基于真实群聊模式的默认值
        if 7 <= hour <= 9:  # 早高峰（上班、上学时间）
            return random.uniform(25, 45)
        elif 11 <= hour <= 13:  # 午间高峰（午休时间）
            return random.uniform(35, 55)
        elif 17 <= hour <= 19:  # 晚高峰（下班时间）
            return random.uniform(40, 65)
        elif 20 <= hour <= 23:  # 晚上活跃时间
            return random.uniform(45, 75)
        elif 0 <= hour <= 2:  # 深夜
            return random.uniform(10, 25)
        else:  # 白天其他时间
            return random.uniform(8, 20)

    def _get_smart_default_users(self, hour: int) -> float:
        """根据小时获取智能默认用户数。"""
        # 用户数通常是消息数的0.6-0.8倍
        msg_count = self._get_smart_default_msgs(hour)
        return msg_count * random.uniform(0.6, 0.8)

    def update_message_rate(self, message_timestamp: float, user_id: str = None):
        """记录一条新消息并更新频率指标。"""
        self.recent_messages.append(message_timestamp)

        # 记录用户活跃度
        if user_id:
            self.recent_users.add(user_id)

        # 收集历史数据
        self._collect_historical_data(message_timestamp, user_id)

        self._update_focus()

    def _collect_historical_data(self, timestamp: float, user_id: str = None):
        """收集历史数据用于分析。"""
        current_time = time.localtime(timestamp)
        hour = current_time.tm_hour
        date_str = time.strftime("%Y-%m-%d", current_time)

        # 更新小时统计
        if hour not in self.hourly_message_counts:
            self.hourly_message_counts[hour] = []

        # 限制每个小时最多保存30天的历史数据
        if len(self.hourly_message_counts[hour]) >= 30:
            self.hourly_message_counts[hour].pop(0)

        self.hourly_message_counts[hour].append(1)  # 每次调用代表一条消息

        # 更新用户统计
        if user_id and hour not in self.hourly_user_counts:
            self.hourly_user_counts[hour] = []

        if user_id:
            if len(self.hourly_user_counts[hour]) >= 30:
                self.hourly_user_counts[hour].pop(0)
            self.hourly_user_counts[hour].append(1)  # 每次调用代表一个活跃用户

        # 更新每日统计
        if date_str not in self.daily_stats:
            self.daily_stats[date_str] = {
                'total_messages': 0,
                'total_users': 0,
                'hourly_breakdown': {h: 0 for h in range(24)}
            }

        self.daily_stats[date_str]['total_messages'] += 1
        self.daily_stats[date_str]['hourly_breakdown'][hour] += 1

        if user_id:
            self.daily_stats[date_str]['total_users'] += 1

        # 定期保存数据（每10分钟或100条消息保存一次）
        if len(self.recent_messages) % 100 == 0 or time.time() - getattr(self, '_last_save_time', 0) > 600:
            self._save_historical_data()

    def _save_historical_data(self):
        """保存历史数据到状态管理器。"""
        if not self.state_manager:
            return

        historical_data = {
            'hourly_message_counts': self.hourly_message_counts,
            'hourly_user_counts': self.hourly_user_counts,
            'daily_stats': self.daily_stats,
            'last_updated': time.time()
        }

        self.state_manager.set(f"frequency_data_{self.group_id}", historical_data)
        self._last_save_time = time.time()
        print(f"为群组 {self.group_id} 保存了历史数据。")

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
