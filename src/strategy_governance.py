from __future__ import annotations

import argparse
from pathlib import Path

from oracle.application.strategy_intelligence import (
    load_parameter_change_requests,
    promote_approved_requests,
    summarize_parameter_change_registry,
    update_request_status_by_id,
)


def _default_registry_file() -> Path:
    return Path("registry/parameter_change_requests.jsonl")


def command_summary(registry_file: Path) -> int:
    summary = summarize_parameter_change_registry(registry_file)
    print(summary)
    return 0


def command_list(registry_file: Path) -> int:
    records = load_parameter_change_requests(registry_file)
    for record in records:
        print(
            {
                "request_id": record.get("request_id"),
                "status": record.get("status"),
                "is_valid": record.get("validation", {}).get("is_valid") if isinstance(record.get("validation"), dict) else None,
                "promoted": record.get("promoted", False),
            }
        )
    return 0


def command_set_status(registry_file: Path, request_id: str, status: str) -> int:
    updated = update_request_status_by_id(registry_file, request_id, status)
    print({"updated": updated, "request_id": request_id, "status": status})
    return 0 if updated else 1


def command_promote(registry_file: Path, output_dir: Path) -> int:
    output_path = promote_approved_requests(registry_file, output_dir)
    if output_path is None:
        print({"promoted": False, "reason": "no-approved-valid-requests"})
        return 0
    print({"promoted": True, "config": str(output_path)})
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Strategy governance CLI")
    parser.add_argument("command", choices=["summary", "list", "set-status", "promote"])
    parser.add_argument("--registry", default=str(_default_registry_file()))
    parser.add_argument("--request-id", default="")
    parser.add_argument("--status", default="pending")
    parser.add_argument("--output-dir", default="reports/strategy-configs")
    args = parser.parse_args()

    registry_file = Path(args.registry)

    if args.command == "summary":
        return command_summary(registry_file)

    if args.command == "list":
        return command_list(registry_file)

    if args.command == "set-status":
        return command_set_status(registry_file, args.request_id, args.status)

    return command_promote(registry_file, Path(args.output_dir))


if __name__ == "__main__":
    raise SystemExit(main())
