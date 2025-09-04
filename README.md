# AstrBot Group Chat Plugin

一个实现高级群聊交互模式的AstrBot插件，包含专注聊天、多种回复生成方式和动态回复意愿管理。

## 功能特性

### 🎯 核心功能

1. **智能回复系统**
   - 动态回复意愿计算
   - 兴趣度评估（"守门员"机制）
   - 疲劳管理防止话痨
   - 灵活的回复生成

2. **双模式聊天**
   - **普通聊天模式**：轻量级后台处理
     - 经典模式：简单直接的回复意愿计算
     - 专注模式：复杂拟人的个人化意愿计算
   - **专注聊天模式**：深度思考循环
     - 观察-处理-规划-行动的完整流程
     - 并行处理器整合信息

3. **记忆系统集成**（可选）
   - 与MemoraConnectPlugin插件集成
   - 基于历史交互的个性化回复
   - 用户印象和关系管理

### 🧠 智能特性

- **兴趣度评估**：分析消息类型、内容长度、交互性等
- **疲劳管理**：自动控制回复频率，避免刷屏
- **模式切换**：根据聊天激烈程度自动切换模式
- **个性化回复**：基于用户关系和聊天历史的定制回复

## 安装使用

### 1. 安装插件

将插件文件夹放置到AstrBot的`data/plugins/`目录下。

### 2. 配置插件

在AstrBot管理面板中配置插件参数，主要包括：

- **基础配置**：插件开关、调试模式
- **模式配置**：专注聊天阈值、模式切换冷却时间
- **回复意愿配置**：经典模式和专注模式的参数调整
- **兴趣度评估配置**：各项评估因素的权重
- **疲劳管理配置**：回复次数限制、恢复时间等
- **记忆系统配置**：记忆集成开关、影响权重等

### 3. 使用插件

插件会自动处理群聊消息，无需手动干预。你可以使用以下命令查看统计信息：

```
/groupchat_stats
```

## 配置说明

### 重要配置项

#### 基础配置
- `enable_plugin`: 是否启用插件
- `debug_mode`: 调试模式开关

#### 模式配置
- `enable_focused_chat`: 是否启用专注聊天模式
- `focused_chat_threshold`: 专注聊天激活阈值（0-1）
- `mode_switch_cooldown`: 模式切换冷却时间（秒）

#### 回复意愿配置
- `classic_mode_enabled`: 启用经典模式
- `focused_mode_enabled`: 启用专注模式
- `response_probability_multiplier`: 回复概率倍数

#### 兴趣度评估配置
- `interest_threshold`: 兴趣度阈值
- `keyword_weight`: 关键词权重
- `context_weight`: 上下文权重
- `sender_weight`: 发送者权重
- `time_weight`: 时间权重

#### 疲劳管理配置
- `max_replies_in_session`: 单次会话最大回复数
- `fatigue_recovery_time`: 疲劳恢复时间（秒）
- `typing_simulation_enabled`: 启用打字模拟

#### 记忆系统配置
- `enable_memory_integration`: 启用记忆系统集成
- `memory_influence_weight`: 记忆系统影响权重
- `memory_recall_limit`: 记忆回忆数量限制

## 工作原理

### 1. 消息处理流程

```
群聊消息 → 兴趣度评估 → 模式判断 → 回复意愿计算 → 生成回复 → 发送消息
```

### 2. 专注聊天模式

当消息兴趣度超过阈值时，插件会进入专注聊天模式：

1. **观察阶段**：收集消息信息和上下文
2. **处理阶段**：并行处理各种信息（工作记忆、关系、工具、表达风格）
3. **规划阶段**：基于处理结果决定行动方案
4. **行动阶段**：执行回复或其他行动

### 3. 回复意愿计算

#### 经典模式
- 基于整个聊天的回复意愿
- 被@或感兴趣话题时意愿上升
- 回复后意愿大幅衰减防刷屏

#### 专注模式
- 针对每个人的独立回复意愿
- 考虑群聊热度、连续对话、说话频率
- 包含疲劳机制避免过度回复

## 依赖要求

- Python 3.8+
- AstrBot 3.4.0+
- aiohttp>=3.9.0（已在requirements.txt中）

### 可选依赖

- MemoraConnectPlugin：用于记忆系统功能

## 开发说明

### 项目结构

```
astrbot_plugin_group_chat/
├── main.py                 # 插件主入口
├── metadata.yaml          # 插件元数据
├── requirements.txt       # 依赖列表
├── README.md              # 说明文档
├── config/                # 配置模块
│   ├── __init__.py
│   ├── plugin_config.py   # 配置管理
│   └── _conf_schema.json  # 配置界面定义
└── core/                  # 核心模块
    ├── __init__.py
    ├── chat_manager.py    # 聊天管理器
    ├── mode_manager.py    # 模式管理器
    ├── interest_evaluator.py  # 兴趣度评估器
    ├── reply_generator.py     # 回复生成器
    ├── fatigue_manager.py     # 疲劳管理器
    └── memory_integration.py  # 记忆系统集成
```

### 核心模块说明

- **ChatManager**：核心聊天管理，处理消息评估和回复生成
- **ModeManager**：模式管理，切换普通聊天和专注聊天模式
- **InterestEvaluator**：兴趣度评估，"守门员"机制
- **ReplyGenerator**：回复生成，灵活的回复内容生成
- **FatigueManager**：疲劳管理，防止话痨
- **MemoryIntegration**：记忆系统集成，与MemoraConnectPlugin交互

## 注意事项

1. **性能考虑**：插件会维护用户和群组状态，内存使用会随活跃度增长
2. **隐私保护**：记忆系统功能默认关闭，需手动启用
3. **配置调优**：建议根据实际使用场景调整各项参数
4. **调试模式**：遇到问题时可开启调试模式查看详细日志

## 更新日志

### v1.0.0
- 初始版本发布
- 实现基础群聊交互功能
- 支持双模式聊天
- 集成记忆系统（可选）
- 提供完整的配置管理

## 许可证

MIT License

## 作者

qa296
