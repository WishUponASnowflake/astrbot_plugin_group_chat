# AstrBot 群聊插件 (astrbot_plugin_group_chat)

一个高级群聊交互插件，能像真人一样主动参与对话，实现拟人化的主动交互体验。

## 🌟 主要特性

### 核心功能
- **智能回复决策**：基于多种因素计算回复意愿，包括用户印象、群活跃度、疲劳度等
- **读空气功能**：使用LLM判断聊天氛围，决定是否回复，避免打扰
- **专注聊天模式**：支持与特定用户的深度对话
- **疲劳系统**：防止过度回复，保持自然交互
- **观察模式**：在低活跃度群组中自动进入观察状态

## 📦 安装

### 环境要求
- AstrBot >= 3.4.0
- Python >= 3.8

### 安装步骤
1. 将插件克隆到AstrBot的plugins目录：
```bash
cd AstrBot/data/plugins
git clone https://github.com/qa296/astrbot_plugin_group_chat.git
```

2. 在AstrBot WebUI的插件管理页面启用插件

3. 根据需要配置插件参数

## ⚙️ 配置说明

### 基础配置
- `list_mode`: 名单模式（blacklist/whitelist）
- `groups`: 群组名单列表
- `base_probability`: 基础回复概率 (0.0-1.0)
- `willingness_threshold`: 回复意愿阈值 (0.0-1.0)
- `max_consecutive_responses`: 最大连续回复次数

### 高级功能
- `air_reading_enabled`: 启用读空气功能
- `focus_chat_enabled`: 启用专注聊天
- `fatigue_enabled`: 启用疲劳系统
- `memory_enabled`: 启用记忆系统（需要memora_connect插件）
- `impression_enabled`: 启用印象系统（需要memora_connect插件）

### 系统参数
- `fatigue_decay_rate`: 疲劳度衰减率 (0.0-1.0)
- `fatigue_reset_interval`: 疲劳度重置间隔（小时）
- `observation_mode_threshold`: 观察模式阈值

## 🚀 使用方法

### 管理指令
- `/群聊状态` - 查看插件状态和统计信息
- `/群聊重置` - 重置所有状态（管理员）
- `/群聊配置` - 查看或修改配置（管理员）

### 配置示例
```
/群聊配置 set base_probability 0.5
/群聊配置 set air_reading_enabled true
/群聊配置 set max_consecutive_responses 5
```

## 📁 文件结构

```
astrbot_plugin_group_chat/
├── main.py                 # 主插件文件
├── metadata.yaml          # 插件元数据
├── _conf_schema.json      # 配置模式定义
├── requirements.txt       # 依赖声明
├── README.md             # 说明文档
└── src/                  # 源代码目录
    ├── state_manager.py      # 状态管理器
    ├── context_analyzer.py   # 上下文分析器
    ├── response_engine.py    # 回复引擎
    ├── willingness_calculator.py  # 意愿计算器
    ├── interaction_manager.py    # 交互管理器
    ├── focus_chat_manager.py     # 专注聊天管理
    ├── fatigue_system.py         # 疲劳系统
    ├── impression_manager.py     # 印象管理器
    ├── memory_integration.py     # 记忆集成
    ├── group_list_manager.py     # 群组管理
    └── utils.py                 # 工具函数
```


## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📞 联系

- GitHub: https://github.com/qa296/astrbot_plugin_group_chat
- AstrBot社区: https://github.com/AstrBotDevs/AstrBot
