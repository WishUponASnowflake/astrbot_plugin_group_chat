# AstrBot 高级群聊插件 (astrbot_plugin_group_chat)

![版本](https://img.shields.io/badge/version-1.0.0-blue)![作者](https://img.shields.io/badge/author-qa296-brightgreen)
[![GitHub antd-design-blazor](https://img.shields.io/github/stars/qa296/astrbot_plugin_group_chat?style=social)](https://github.com/qa296/astrbot_plugin_group_chat)

一个为 [AstrBot](https://github.com/your-astrbot-repo-link) 设计的高级群聊交互插件，它能像真人一样分析群聊氛围、评估对话兴趣，并主动参与对话，旨在实现真正拟人化的、沉浸式的主动交互体验。

## ✨ 项目特色

- **拟人化交互**: 摆脱传统问答机器人的被动形象，能够主动、自然地融入群聊。
- **双模对话系统**:
    - **经典模式 (Classic Mode)**: 基于回复意愿和兴趣度的常规聊天模式。
    - **专注模式 (Focused Mode)**: 当检测到高热度或高相关性对话时，机器人会进入此模式，更积极地参与连续对话。
- **动态回复意愿**: 综合考虑是否被`@`、话题兴趣度、时间衰减等多种因素，动态计算回复意愿，让交互更真实。
- **兴趣度评估**: 通过关键词、上下文、发送者和时间等多维度权重，智能评估机器人对当前话题的“兴趣”。
- **疲劳管理系统**: 模拟真人的聊天疲劳，在长时间高强度对话后会自动降低活跃度，避免刷屏。
- **高度可配置**: 几乎所有功能参数，如意愿阈值、疲劳度、兴趣权重等，都可通过配置文件进行详细定制。
- **记忆系统集成 (可选)**: 可集成外部记忆系统，让机器人根据印象调整回复意愿，对话更具连续性。

## ⚙️ 安装

1.  确保您已经成功部署了 AstrBot。
2.  将本项目克隆或下载到 AstrBot 的 `plugins` 目录下。
3.  重启 AstrBot，插件将被自动加载。

## 🔧 配置

插件的详细配置位于 `config/plugin_config.py` 文件中，您也可以通过 AstrBot 提供的配置文件覆盖默认设置。

以下是核心配置项说明：

| 配置项                          | 类型    | 默认值 | 描述                                           |
| ------------------------------- | ------- | ------ | ---------------------------------------------- |
| `enable_plugin`                 | `bool`  | `True` | 是否启用插件。                                 |
| `debug_mode`                    | `bool`  | `False`| 启用后会输出详细的决策日志。                   |
| `enable_focused_chat`           | `bool`  | `True` | 是否启用“专注聊天”模式。                       |
| `focused_chat_threshold`        | `float` | `0.7`  | 激活专注模式的兴趣度阈值。                     |
| `classic_base_willingness`      | `float` | `0.3`  | 经典模式下的基础回复意愿。                     |
| `focused_base_willingness`      | `float` | `0.4`  | 专注模式下的基础回复意愿。                     |
| `fatigue_manager_enabled`       | `bool`  | `True` | 是否启用疲劳管理。                             |
| `max_replies_in_session`        | `int`   | `10`   | 单次会话（未进入疲劳前）的最大回复数。         |
| `fatigue_recovery_time`         | `int`   | `300`  | 疲劳状态恢复所需时间（秒）。                   |
| `enable_memory_integration`     | `bool`  | `False`| 是否启用记忆系统集成。                         |

更多详细配置，请直接查阅 [`config/plugin_config.py`](config/plugin_config.py) 文件。

## 🚀 使用

插件加载后将自动接管所有群聊消息。它会在后台默默分析每一条消息，并根据内部的决策逻辑判断是否以及如何进行回复。

您无需进行任何额外的操作，只需观察它在群聊中的表现即可。

## 🤝 贡献

欢迎通过以下方式为本项目做出贡献：

-   **提交 Issue**: 如果您发现了 Bug 或有任何功能建议，请随时提交 Issue。
-   **发起 Pull Request**: 我们非常欢迎您通过 PR 的方式为项目贡献代码。

