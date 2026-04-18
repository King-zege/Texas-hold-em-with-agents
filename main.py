"""Main entry point for poker training system."""

import argparse
import sys
from pathlib import Path

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from engine.game import Game
from analysis.analysis_agent import AnalysisAgent, print_analysis
from memory.history_store import HistoryStore
from memory.decision_logger import DecisionLogger


def main():
    parser = argparse.ArgumentParser(description="德州扑克训练系统")
    parser.add_argument("--config", default="config/game_config.yaml", help="游戏配置文件路径")
    parser.add_argument("--hands", type=int, help="要打的手数 (覆盖配置)")
    parser.add_argument("--interactive", action="store_true", help="每手牌后询问是否继续")
    parser.add_argument("--seed", type=int, help="随机种子 (覆盖配置)")
    parser.add_argument("--show-holes", action="store_true", help="显示所有玩家手牌")
    parser.add_argument("--analyze", action="store_true", help="分析手牌历史")
    parser.add_argument("--history", default="hand_history.jsonl", help="手牌历史文件路径")
    parser.add_argument("--clear-history", action="store_true", help="游戏开始前清除历史记录")
    parser.add_argument("--session-id", type=str, help="设置session ID（也可游戏开始时输入）")
    args = parser.parse_args()

    # Check if config exists
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"错误: 配置文件 {args.config} 不存在")
        sys.exit(1)

    # If --analyze, load and analyze existing history
    if args.analyze:
        analyze_history(args.history, config_path)
        return

    # Initialize game with optional session_id
    print(f"加载配置: {args.config}")
    game = Game(args.config, session_id=args.session_id)

    # If no session_id from CLI, prompt for one
    if not args.session_id:
        try:
            session_input = input("\n请输入本场游戏ID（如 3892）: ").strip()
            if session_input:
                game.session_id = session_input
                # Regenerate filenames with new session_id
                import os
                base_history = game.config.get("session", {}).get("history_file", "hand_history.jsonl")
                base_log = game.config.get("session", {}).get("decision_log", "decision_log.txt")
                game.history_store = HistoryStore(os.path.splitext(base_history)[0] + f"_{session_input}" + os.path.splitext(base_history)[1])
                game.decision_logger = DecisionLogger(os.path.splitext(base_log)[0] + f"_{session_input}" + os.path.splitext(base_log)[1])
                print(f"游戏记录将保存到: decision_log_{session_input}.txt, hand_history_{session_input}.jsonl\n")
        except (EOFError, KeyboardInterrupt):
            print("\n使用默认文件名...")
            session_input = ""

    # Clear history if requested
    if args.clear_history:
        print("清除历史记录...")
        game.history_store.clear()
        game.decision_logger.clear()

    # Override seed if specified
    if args.seed is not None:
        game.config["session"]["seed"] = args.seed
        print(f"使用随机种子: {args.seed}")

    # Override hands if specified
    num_hands = args.hands
    if num_hands is None:
        num_hands = game.config.get("session", {}).get("num_hands", 10)

    # Play session
    mode = f" {num_hands} 手牌" if not args.interactive else "无限模式"
    print(f"\n开始{mode}...\n")
    results = game.play_session(num_hands, interactive=args.interactive)

    # Summary
    print(f"\n{'='*50}")
    print("会话结束")
    print(f"{'='*50}")
    for p in game.players:
        print(f"  {p['id']}: {p['stack_bb']:.1f}BB (初始: {p['initial_stack_bb']:.1f}BB)")

    # Print history file info
    print(f"\n手牌历史已保存到: {game.history_store.filepath}")
    print(f"决策日志已保存到: {game.decision_logger.filepath}")


def analyze_history(history_file: str, config_path: str) -> None:
    """Analyze hand history from file."""
    from memory.history_store import HistoryStore
    from pathlib import Path

    history_path = Path(history_file)
    if not history_path.exists():
        print(f"错误: 手牌历史文件 {history_file} 不存在")
        print("请先运行游戏生成历史记录: python main.py --hands 5")
        sys.exit(1)

    print(f"加载手牌历史: {history_file}")
    store = HistoryStore(history_file)
    histories = store.load_all()

    if not histories:
        print("没有找到手牌历史记录")
        return

    print(f"找到 {len(histories)} 手牌历史\n")

    # Initialize style registry
    styles_dir = Path(config_path).parent / "styles"
    from strategy.style_profile import StyleRegistry
    registry = StyleRegistry(str(styles_dir))

    # Create analysis agent
    agent = AnalysisAgent(registry)

    # Analyze each hand
    for history in histories:
        analysis = agent.analyze_hand(history)
        print_analysis(analysis)


if __name__ == "__main__":
    main()
