from __future__ import annotations

import argparse
import json
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pageanchor")
    sub = parser.add_subparsers(dest="cmd", required=True)

    ingest_parser = sub.add_parser("ingest", help="download, render, layout, and index the corpus")
    ingest_parser.add_argument("--all", action="store_true")
    ingest_parser.add_argument("--doc-id")
    ingest_parser.add_argument("--visual", action="store_true")

    ask_parser = sub.add_parser("ask", help="answer a question with citations or abstain")
    ask_parser.add_argument("question")
    ask_parser.add_argument("--mode", default="hybrid")

    eval_parser = sub.add_parser("eval", help="score gold questions")
    eval_parser.add_argument("--gold", default="corpus/eval/gold_questions.jsonl")
    eval_parser.add_argument("--modes", default="text,visual,hybrid,hybrid+verify")
    eval_parser.add_argument("--out", required=True)

    args = parser.parse_args(argv)
    if args.cmd == "ingest":
        from pageanchor.ingest import ingest_all

        for result in ingest_all(doc_id=args.doc_id, all_docs=args.all, visual=args.visual):
            print(json.dumps(result), flush=True)
        return 0
    if args.cmd == "ask":
        from pageanchor.config import load_settings
        from pageanchor.ground.answer import grounded_answer

        try:
            print(
                grounded_answer(
                    args.question,
                    args.mode,
                    strict=load_settings().strict_verify,
                ).model_dump_json(indent=2)
            )
        except FileNotFoundError as exc:
            print(exc, file=sys.stderr)
            return 1
        return 0
    if args.cmd == "eval":
        from pageanchor.eval.run import run_eval

        try:
            results = run_eval(args.gold, args.modes.split(","), args.out)
        except FileNotFoundError as exc:
            print(exc, file=sys.stderr)
            return 1
        print(json.dumps({mode: payload["metrics"] for mode, payload in results.items()}, indent=2))
        return 0
    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
