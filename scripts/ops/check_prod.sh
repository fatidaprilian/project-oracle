#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-https://project-oracle-133425616833.asia-southeast2.run.app}"

printf "Checking Project Oracle production at %s\n" "$BASE_URL"

health_json="$(curl -fsS "$BASE_URL/health")"
readiness_json="$(curl -fsS "$BASE_URL/api/v1/config/readiness")"
connections_json="$(curl -fsS "$BASE_URL/api/v1/config/connections")"

python3 - <<'PY' "$health_json" "$readiness_json" "$connections_json"
import json
import sys

health = json.loads(sys.argv[1])
readiness = json.loads(sys.argv[2])
connections = json.loads(sys.argv[3])

failures: list[str] = []

if health.get("status") != "healthy":
    failures.append("health.status is not healthy")

if readiness.get("postgres_enabled") and not readiness.get("postgres_dsn_configured"):
    failures.append("postgres is enabled but DSN is missing")

if readiness.get("redis_enabled") and not readiness.get("redis_url_configured"):
    failures.append("redis is enabled but URL is missing")

postgres = connections.get("postgres", {})
if postgres.get("enabled") and not postgres.get("reachable"):
    failures.append(f"postgres not reachable: {postgres.get('detail', 'unknown error')}")

redis = connections.get("redis", {})
if redis.get("enabled") and not redis.get("reachable"):
    failures.append(f"redis not reachable: {redis.get('detail', 'unknown error')}")

print("Health:", health)
print("Readiness:", readiness)
print("Connections:", connections)

if failures:
    print("\nFAILED checks:")
    for failure in failures:
        print("-", failure)
    raise SystemExit(1)

print("\nAll production checks passed.")
PY

curl -fsS -o /dev/null "$BASE_URL/docs"
printf "Swagger docs endpoint reachable.\n"
