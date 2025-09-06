import json
import os
import time
from typing import Dict, Any, Optional
from pathlib import Path

from astrbot.api import logger
from astrbot.api.star import Context

class StateManager:
    """状态管理器 - 负责插件状态的持久化存储"""
    
    def __init__(self, context: Context, config: Any):
        self.context = context
        self.config = config
        
        # 获取数据目录路径
        self.data_dir = Path(context.get_config().get("data_dir", "data"))
        self.plugin_data_dir = self.data_dir / "astrbot_plugin_group_chat"
        
        # 确保数据目录存在
        self.plugin_data_dir.mkdir(parents=True, exist_ok=True)
        
        # 状态文件路径
        self.state_file = self.plugin_data_dir / "state.json"
        
        # 内存中的状态
        self._state_cache: Dict[str, Any] = {}
        
        # 加载已有状态
        self._load_state()
        
        logger.info(f"状态管理器初始化完成，数据目录: {self.plugin_data_dir}")
    
    def _load_state(self):
        """从文件加载状态"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    self._state_cache = json.load(f)
                logger.info(f"已从 {self.state_file} 加载状态数据")
            except Exception as e:
                logger.error(f"加载状态文件失败: {e}")
                self._state_cache = {}
        else:
            logger.info("状态文件不存在，使用空状态")
            self._state_cache = {}
    
    def _save_state(self):
        """保存状态到文件"""
        try:
            # 创建备份
            if self.state_file.exists():
                backup_file = self.state_file.with_suffix('.json.backup')
                backup_file.write_text(self.state_file.read_text(encoding='utf-8'), encoding='utf-8')
            
            # 保存新状态
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self._state_cache, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"状态已保存到 {self.state_file}")
        except Exception as e:
            logger.error(f"保存状态文件失败: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取状态值"""
        return self._state_cache.get(key, default)
    
    def set(self, key: str, value: Any):
        """设置状态值"""
        self._state_cache[key] = value
        self._save_state()
    
    def update(self, key: str, value: Any, save: bool = True):
        """更新状态值（可选择是否立即保存）"""
        self._state_cache[key] = value
        if save:
            self._save_state()
    
    def delete(self, key: str):
        """删除状态值"""
        if key in self._state_cache:
            del self._state_cache[key]
            self._save_state()
    
    def get_interaction_modes(self) -> Dict[str, str]:
        """获取交互模式状态"""
        return self.get("interaction_modes", {})
    
    def set_interaction_mode(self, group_id: str, mode: str):
        """设置交互模式"""
        modes = self.get_interaction_modes()
        modes[group_id] = mode
        self.set("interaction_modes", modes)
    
    def get_focus_targets(self) -> Dict[str, str]:
        """获取专注聊天目标"""
        return self.get("focus_targets", {})
    
    def set_focus_target(self, group_id: str, user_id: str):
        """设置专注聊天目标"""
        targets = self.get_focus_targets()
        targets[group_id] = user_id
        self.set("focus_targets", targets)
    
    def remove_focus_target(self, group_id: str):
        """移除专注聊天目标"""
        targets = self.get_focus_targets()
        if group_id in targets:
            del targets[group_id]
            self.set("focus_targets", targets)
    
    def get_fatigue_data(self) -> Dict[str, float]:
        """获取疲劳度数据"""
        return self.get("fatigue_data", {})
    
    def update_fatigue(self, user_id: str, fatigue_value: float):
        """更新疲劳度"""
        fatigue_data = self.get_fatigue_data()
        fatigue_data[user_id] = fatigue_value
        self.set("fatigue_data", fatigue_data)
    
    def get_conversation_counts(self) -> Dict[str, Dict[str, int]]:
        """获取对话计数"""
        return self.get("conversation_counts", {})
    
    def increment_conversation_count(self, group_id: str, user_id: str):
        """增加对话计数"""
        counts = self.get_conversation_counts()
        if group_id not in counts:
            counts[group_id] = {}
        counts[group_id][user_id] = counts[group_id].get(user_id, 0) + 1
        self.set("conversation_counts", counts)
    
    def get_last_activity(self, key: str) -> float:
        """获取指定键的最后活动时间"""
        return self.get("last_activity", {}).get(key, 0.0)

    def update_last_activity(self, key: str, timestamp: float = None):
        """更新最后活动时间"""
        if timestamp is None:
            timestamp = time.time()
        activity = self.get("last_activity", {})
        activity[key] = timestamp
        self.set("last_activity", activity)

    def get_user_impression(self, user_id: str) -> Dict[str, Any]:
        """获取用户印象"""
        return self.get("user_impressions", {}).get(user_id, {})

    def get_focus_target(self, group_id: str) -> Optional[str]:
        """获取专注聊天目标"""
        return self.get_focus_targets().get(group_id)

    def clear_focus_target(self, group_id: str):
        """清除专注聊天目标"""
        targets = self.get_focus_targets()
        if group_id in targets:
            del targets[group_id]
            self.set("focus_targets", targets)

    def get_focus_response_count(self, group_id: str) -> int:
        """获取专注聊天回复计数"""
        return self.get("focus_response_counts", {}).get(group_id, 0)

    def increment_focus_response_count(self, group_id: str):
        """增加专注聊天回复计数"""
        counts = self.get("focus_response_counts", {})
        counts[group_id] = counts.get(group_id, 0) + 1
        self.set("focus_response_counts", counts)

    def clear_focus_response_count(self, group_id: str):
        """清除专注聊天回复计数"""
        counts = self.get("focus_response_counts", {})
        if group_id in counts:
            del counts[group_id]
            self.set("focus_response_counts", counts)
    
    def get_consecutive_responses(self) -> Dict[str, int]:
        """获取连续回复计数"""
        return self.get("consecutive_responses", {})
    
    def increment_consecutive_response(self, group_id: str):
        """增加连续回复计数"""
        responses = self.get_consecutive_responses()
        responses[group_id] = responses.get(group_id, 0) + 1
        self.set("consecutive_responses", responses)
    
    def reset_consecutive_response(self, group_id: str):
        """重置连续回复计数"""
        responses = self.get_consecutive_responses()
        if group_id in responses:
            responses[group_id] = 0
            self.set("consecutive_responses", responses)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "interaction_modes_count": len(self.get_interaction_modes()),
            "focus_targets_count": len(self.get_focus_targets()),
            "fatigue_users_count": len(self.get_fatigue_data()),
            "conversation_groups_count": len(self.get_conversation_counts()),
            "last_activity_count": len(self.get("last_activity", {})),
            "consecutive_responses_count": len(self.get_consecutive_responses()),
            "state_file": str(self.state_file),
            "state_file_exists": self.state_file.exists(),
            "state_file_size": self.state_file.stat().st_size if self.state_file.exists() else 0
        }
    
    def clear_all_state(self):
        """清空所有状态"""
        self._state_cache.clear()
        self._save_state()
        logger.info("所有状态已清空")
    
    def backup_state(self, backup_name: str = None) -> str:
        """备份状态到指定文件"""
        if backup_name is None:
            backup_name = f"state_backup_{int(time.time())}.json"
        
        backup_file = self.plugin_data_dir / backup_name
        
        try:
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(self._state_cache, f, ensure_ascii=False, indent=2)
            
            logger.info(f"状态已备份到 {backup_file}")
            return str(backup_file)
        except Exception as e:
            logger.error(f"备份状态失败: {e}")
            raise
    
    def restore_state(self, backup_file_path: str):
        """从备份文件恢复状态"""
        backup_file = Path(backup_file_path)
        
        if not backup_file.exists():
            raise FileNotFoundError(f"备份文件不存在: {backup_file}")
        
        try:
            with open(backup_file, 'r', encoding='utf-8') as f:
                backup_state = json.load(f)
            
            # 验证备份文件格式
            if not isinstance(backup_state, dict):
                raise ValueError("备份文件格式错误")
            
            # 恢复状态
            self._state_cache = backup_state
            self._save_state()
            
            logger.info(f"状态已从 {backup_file} 恢复")
        except Exception as e:
            logger.error(f"恢复状态失败: {e}")
            raise
