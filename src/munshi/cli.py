"""Command line: `munshi close`, `munshi score`, `munshi benchmark`."""

import argparse
import json
from datetime import datetime
from pathlib import Path

from munshi import tracing
from munshi.config import ROOT, settings

DEFAULT_MONTH = ROOT / "data/demo/studio-kaveri/2026-09"
DEFAULT_KEY = ROOT / "data/answer_key/studio-kaveri-2026-09.json"


def main() -> None:
    import sys
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    p = argparse.ArgumentParser(prog="munshi")
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("close", help="close a month")
    c.add_argument("--version", choices=["v1", "v2"], default="v2")
    c.add_argument("--month", type=Path, default=DEFAULT_MONTH)
    c.add_argument("--out", type=Path)
    c.add_argument("--live-actions", action="store_true", help="create real Dodo (test mode) payment links")
    c.add_argument("--no-peers", action="store_true")
    s = sub.add_parser("score", help="score a run against the answer key")
    s.add_argument("run_dir", type=Path)
    s.add_argument("--key", type=Path, default=DEFAULT_KEY)
    b = sub.add_parser("benchmark", help="score the document reader on real SROIE receipts")
    b.add_argument("--n", type=int, default=30)
    b.add_argument("--version", choices=["v1", "v2"], default="v2")
    args = p.parse_args()

    if args.cmd == "close":
        from munshi import close, score
        tracing.init(args.version)
        out = args.out or ROOT / "runs" / f"{datetime.now():%Y%m%d-%H%M%S}-{args.version}-{settings.llm_provider}"
        session = f"close-{args.month.parent.name}-{args.month.name}-{args.version}-{datetime.now():%H%M%S}"
        with tracing.run(f"munshi-close-{args.version}", session_id=session, end_user_id=args.month.parent.name):
            if args.version == "v1":
                close.close_v1(args.month, out)
            else:
                close.close_v2(args.month, out, live_actions=args.live_actions, with_peers=not args.no_peers)
        tracing.shutdown()
        result = score.score(out, DEFAULT_KEY)
        (out / "score.json").write_text(json.dumps(result, indent=1), encoding="utf-8")
        print(json.dumps({k: v for k, v in result.items() if k != "traps"}, indent=1))
        print("session:", session, "| out:", out)
    elif args.cmd == "score":
        from munshi import score
        print(json.dumps(score.score(args.run_dir, args.key), indent=1))
    elif args.cmd == "benchmark":
        from munshi import benchmark
        tracing.init(f"bench-{args.version}")
        print(json.dumps(benchmark.run(args.n, args.version), indent=1))
        tracing.shutdown()


if __name__ == "__main__":
    main()
