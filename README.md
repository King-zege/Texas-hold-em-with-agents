# 多 Agent 德州扑克训练系统

基于 Python 的多 Agent 德州扑克训练/模拟系统，支持不同风格的玩家、牌局历史记录和复盘分析。

## 功能特性

- **多 Agent 架构**：顺序式 Agent 工作流，每个 Agent 独立决策
- **多种玩家风格**：TAG、LAG、TP、LP、Nit、Calling Station、Maniac、Balanced
- **完整扑克流程**：翻前 → 翻牌 → 转牌 → 河牌 → 摊牌
- **边池计算**：支持多人全入产生的边池
- **手牌历史**：JSONL 格式存储完整牌局记录
- **决策日志**：详细记录每个 Agent 的决策过程
- **复盘分析**：分析 Agent 决策是否符合其风格

## 安装

```bash
pip install treys pyyaml
```

## 运行

### 基础运行
```bash
python main.py
```

### 指定手数
```bash
python main.py --hands 10
```

### 设置随机种子（可复现）
```bash
python main.py --hands 5 --seed 42
```

### 分析历史记录
```bash
python main.py --analyze --history hand_history.jsonl
```

## 输出文件

- `hand_history.jsonl` - 手牌历史记录（JSONL 格式）
- `decision_log.txt` - 决策日志（详细记录每个决策）

## 配置文件

编辑 `config/game_config.yaml` 可配置：
- 玩家人数和座位
- 各玩家风格
- 各玩家筹码深度
- 小盲/大盲金额

## 项目结构

```
poker/
├── engine/          # 游戏引擎
│   ├── card.py          # 扑克牌表示
│   ├── deck.py         # 牌堆管理
│   ├── action.py       # 动作类型
│   ├── betting.py      # 下注轮逻辑
│   ├── hand.py        # 单手牌流程
│   ├── game.py        # 游戏会话
│   ├── pot.py         # 底池计算
│   └── hand_evaluator.py  # 手牌评估
├── agent/           # Agent 模块
│   ├── base_agent.py     # 基类
│   ├── rule_agent.py     # 规则 Agent
│   ├── style_agent.py    # 风格 Agent
│   ├── observation.py    # 观察数据
│   └── legal_action_filter.py  # 法律行动过滤
├── strategy/        # 策略模块
│   ├── style_profile.py     # 风格配置
│   ├── preflop_table.py     # 翻前手牌强度
│   ├── postflop_heuristic.py  # 翻后手牌强度
│   └── skills/             # 各风格策略指南
│       ├── tag_skills.md
│       ├── lag_skills.md
│       └── ...
├── memory/          # 记忆模块
│   ├── hand_history.py     # 手牌历史
│   ├── history_store.py    # 历史存储
│   └── decision_logger.py  # 决策日志
├── analysis/        # 分析模块
│   ├── analysis_agent.py   # 复盘分析
│   └── decision_review.py  # 决策评审
├── config/          # 配置文件
│   ├── game_config.yaml    # 游戏配置
│   └── styles/            # 风格配置
│       ├── tag.yaml
│       ├── lag.yaml
│       └── ...
└── main.py          # 入口文件
```

## 玩家风格说明

| 风格 | 说明 |
|------|------|
| **TAG** | Tight-Aggressive，紧凶。只玩强牌但打得很激进 |
| **LAG** | Loose-Aggressive，松凶。玩很多牌，非常激进 |
| **TP** | Tight-Passive，紧弱。只玩强牌但打法被动 |
| **LP** | Loose-Passive，松弱。玩很多牌但很少加注 |
| **Nit** | 超紧，极度保守，只玩顶级牌 |
| **Calling Station** | 跟注站，很少弃牌，只看摊牌 |
| **Maniac** | 疯狗，玩每手牌，极度激进 |
| **Balanced** | 均衡，混合策略 |

## 决策日志示例

```
Hand | Street | Player (Position) | Action | Style | Reason
----------------------------------------------------------------------------------------------------
h001 | preflop | Dave (CO) | raise 2.0BB     | balanced | Balanced / Reg - 用强牌加注 (好牌)
h001 | flop    | Dave (CO) | bet 4.5BB      | balanced | Balanced / Reg - 诈唬/施压 (中等牌)
h001 | turn    | Dave (CO) | check          | balanced | Balanced / Reg - 过牌 (弱牌)
```

## 下一步

- Phase 6（可选）：接入 LLM 实现更智能的 Agent
- 扩展锦标赛模式（盲注增长）
- 添加更多风格变种
