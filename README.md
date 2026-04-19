# 多 Agent 德州扑克训练系统

基于 Python 的多 Agent 德州扑克训练/模拟系统，支持不同风格的玩家对战、完整牌局记录和复盘分析。

## 功能特性

- **多 Agent 架构**：支持规则 Agent（StyleAgent）和 LLM Agent 两种决策方式
- **多种玩家风格**：8 种预设风格，模拟不同类型的扑克玩家
- **完整扑克流程**：翻前 → 翻牌 → 转牌 → 河牌 → 摊牌（含边池计算）
- **GTO 策略支持**：LLM Agent 可注入 GTO/纳什均衡策略指导
- **手牌历史**：JSONL 格式存储完整牌局记录
- **决策日志**：详细记录每个 Agent 的决策过程
- **复盘分析**：分析 Agent 决策是否符合其风格定位

## 安装

```bash
pip install treys pyyaml
```

## 运行模式

### 1. 固定手数模式（默认）
指定打多少手牌后结束：
```bash
# 打 10 手牌
python main.py --hands 10

# 设置随机种子（可复现）
python main.py --hands 5 --seed 42
```

### 2. 无限模式
每手牌后询问是否继续：
```bash
python main.py --interactive
```

### 3. 会话 ID 模式
为每次游戏生成独立的记录文件：
```bash
python main.py --hands 10 --session-id test001
```
输出文件：
- `hand_history_test001.jsonl`
- `decision_log_test001.txt`

### 4. 分析历史记录
```bash
python main.py --analyze --history hand_history.jsonl
```

### 5. 其他选项
```bash
python main.py --show-holes   # 显示所有玩家手牌（慎用，会泄露信息）
python main.py --clear-history  # 游戏开始前清除历史记录
```

## 配置文件

编辑 `config/game_config.yaml`：

```yaml
table:
  size: 6                    # 桌台大小（最多玩家数）
  small_blind_bb: 0.5        # 小盲（BB为单位）
  big_blind_bb: 1.0          # 大盲（BB为单位）

players:
  - id: "Alice"             # 玩家 ID
    style: "llm"            # 决策类型：llm / human / 风格名称
    llm_style: "balanced"   # LLM Agent 的风格（当 style=llm 时）
    stack_bb: 100            # 初始筹码（BB为单位）

session:
  num_hands: 10             # 默认手数
  seed: 42                   # 随机种子（设为 null 则随机）
  history_file: "hand_history.jsonl"
  decision_log: "decision_log.txt"
  show_hole_cards: false

# LLM API 配置
llm:
  api_key: "YOUR_API_KEY"    # ⚠️ 填入你的 API Key
  api_base: "https://open.bigmodel.cn/api/paas/v4"  # API 地址
  model: "glm-4-flash"       # 模型名称
  use_skills_in_prompt: true # 是否向 LLM 注入 GTO 策略
```

## 玩家风格说明

在 `config/game_config.yaml` 中设置 `style` 字段，可选风格：

| 风格 | 名称 | 说明 |
|------|------|------|
| `tag` | Tight-Aggressive（紧凶） | 只玩少量强牌，一旦入池就激进加注 |
| `lag` | Loose-Aggressive（松凶） | 玩很多牌，非常激进，喜欢偷盲施压 |
| `balanced` | Balanced（均衡） | 技术全面的常规玩家，紧松和激进程度均衡 |
| `nit` | Ultra-Tight（极紧） | 只玩最高质量的牌，几乎不诈唬 |
| `tp` | Tight-Passive（紧弱） | 只玩强牌但打法被动，多跟注少加注 |
| `lp` | Loose-Passive（松弱） | 玩很多牌但很少加注，被动跟注看摊牌 |
| `calling_station` | Calling Station（跟注站） | 几乎不弃牌也不加注，粘池跟注到底 |
| `maniac` | Maniac（疯狗） | 每手都玩，极度激进，不可预测 |
| `llm` | LLM Agent | 使用大语言模型决策，需配合 `llm_style` 指定风格 |
| `human` | Human（人类） | 交互式输入，等待人类操作 |

### LLM Agent 的风格

当 `style: "llm"` 时，通过 `llm_style` 指定该 LLM 使用的策略风格：

- `llm_style: "balanced"` - 均衡策略
- `llm_style: "tag"` - 紧凶
- `llm_style: "lag"` - 松凶
- `llm_style: "nit"` - 极紧
- 等等（所有 8 种风格都支持）

LLM Agent 会根据选定的风格，在决策时注入对应的 **GTO/纳什均衡策略指导** 到 prompt 中。

## 支持的 API

系统使用 **智谱 AI（BigModel）** 的 OpenAI 兼容 API。

如需切换到其他 OpenAI 兼容 API（如 Claude、OpenAI 等），修改 `config/game_config.yaml` 中的 `llm` 配置段：

```yaml
llm:
  api_key: "YOUR_API_KEY"
  api_base: "https://api.openai.com/v1"   # 切换 API 地址
  model: "gpt-4o-mini"                     # 切换模型
```

## 项目结构

```
poker/
├── engine/                      # 游戏引擎核心
│   ├── card.py                  # 扑克牌表示
│   ├── deck.py                  # 牌堆管理
│   ├── action.py                # 动作类型定义
│   ├── betting.py               # 下注轮逻辑
│   ├── hand.py                  # 单手牌流程
│   ├── game.py                  # 游戏会话管理
│   ├── pot.py                   # 底池和边池计算
│   └── hand_evaluator.py        # 手牌强度评估
├── agent/                       # Agent 模块
│   ├── base_agent.py            # Agent 基类
│   ├── style_agent.py           # 风格 Agent（基于规则的决策）
│   ├── llm_agent.py             # LLM Agent（调用大模型决策）
│   ├── human_agent.py           # 人类玩家 Agent
│   ├── observation.py            # 决策观察信息
│   └── legal_action_filter.py    # 合法动作过滤
├── strategy/                    # 策略模块
│   ├── style_profile.py         # 风格配置数据结构和加载
│   ├── preflop_table.py         # 翻前手牌强度表
│   ├── postflop_heuristic.py    # 翻后手牌强度评估
│   └── skills/                  # 各风格策略指南（GTO 参考）
│       ├── tag_skills.md
│       ├── lag_skills.md
│       ├── balanced_skills.md
│       └── ...
├── memory/                     # 记忆模块
│   ├── hand_history.py          # 手牌历史数据结构
│   ├── history_store.py         # 历史记录存储
│   └── decision_logger.py       # 决策日志
├── analysis/                    # 分析模块
│   ├── analysis_agent.py         # 复盘分析 Agent
│   └── decision_review.py       # 决策评审
├── config/                      # 配置文件
│   ├── game_config.yaml         # 游戏主配置
│   └── styles/                  # 风格配置
│       ├── tag.yaml
│       ├── lag.yaml
│       ├── balanced.yaml
│       └── ...
├── main.py                      # 程序入口
└── requirements.txt             # 依赖包
```

## 输出文件

| 文件 | 说明 | 格式 |
|------|------|------|
| `hand_history_{session}.jsonl` | 手牌历史记录 | JSONL（每行一手牌） |
| `decision_log_{session}.txt` | 决策日志 | 文本 |

### 手牌历史示例

```json
{
  "hand_id": "h001",
  "timestamp": "2026-04-18 20:02:26",
  "table_size": 6,
  "players": [...],
  "hole_cards": {"Alice": ["3♦", "K♦"], "Human": ["6♠", "K♠"], ...},
  "community_cards": ["2♣", "2♠", "8♦", "10♣", "4♥"],
  "actions": [...],
  "pots": [{"amount_bb": 206.5, "winners": [{"player": "Frank", "hand": "三条"}]}],
  "final_stacks": {...}
}
```

## GTO 策略注入说明

LLM Agent 支持在决策时注入 GTO/纳什均衡策略指导：

- **翻前策略**：存储在 `config/styles/{style}.yaml` 的 `gto_preflop` 字段中，包含开池范围、加注尺度、3-bet 策略等
- **翻后策略**：存储在 `strategy/skills/{style}_skills.md` 的 `## GTO 参考` 章节中，包含 C-bet 频率、下注尺度、抓鸡策略等

启用/禁用方式：在 `game_config.yaml` 中设置 `llm.use_skills_in_prompt: true/false`

## 下一步方向

- [ ] 扩展锦标赛模式（盲注递增）
- [ ] 添加更多风格变种
- [ ] 优化 LLM Agent 的解析稳定性
