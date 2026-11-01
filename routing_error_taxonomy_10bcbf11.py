"""（大模型推理场景）梯度累积与有效批量的测量噪声主要来自哪里？用路由与负载分布估计噪声水平，并求出结论仍然稳定的最小样本量。

测量：路由与负载分布（load_imbalance）；协议：失败归类。
仅依赖 Python 标准库。
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from typing import Any

SEP = ','
MEASURE_FIELD = 'load_imbalance'
FAILURE_MODE = '版本漂移'


def _read_rows(path: str, limit: int = 0) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    with open(path, "r", encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line.strip():
                continue
            if SEP and SEP in line:
                label, _, payload = line.partition(SEP)
                rows.append((label.strip(), payload.strip()))
            else:
                rows.append(("", line.strip()))
            if limit and len(rows) >= limit:
                break
    return rows


def _nums(values: list[str]) -> list[float]:
    out: list[float] = []
    for v in values:
        try:
            out.append(float(v))
        except ValueError:
            continue
    return out


def _percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    pos = (len(ordered) - 1) * q
    lo = int(pos)
    hi = min(lo + 1, len(ordered) - 1)
    frac = pos - lo
    return ordered[lo] * (1 - frac) + ordered[hi] * frac



def measure_routing(rows: list[tuple[str, str]]) -> dict:
    """负载分布：分片负载是否均衡。"""
    from collections import Counter

    counts = Counter(label or "unlabeled" for label, _ in rows)
    loads = list(counts.values())
    out: dict = {"metric": "routing", "unit": "倍"}
    if not loads:
        out["load_imbalance"] = None
        return out
    avg = sum(loads) / len(loads)
    out["shard_count"] = len(loads)
    out["max_load"] = max(loads)
    out["avg_load"] = round(avg, 4)
    out["load_imbalance"] = round(max(loads) / avg, 4) if avg else None
    out["balanced"] = bool(avg and max(loads) / avg <= 1.5)
    out["per_shard"] = dict(sorted(counts.items()))
    return out



def measure(rows: list[tuple[str, str]]) -> dict:
    """按测量族分派到具体测量函数。"""
    return measure_routing(rows)



def run_protocol(measure, rows: list[tuple[str, str]], args: argparse.Namespace) -> dict:
    """失败归类：把未达判定阈值的样本归类。"""
    threshold = float(args.threshold or 0)
    buckets: dict[str, list[str]] = {}
    for label, payload in rows:
        value = measure([(label, payload)])
        value = value.get('load_imbalance')
        if not isinstance(value, (int, float)):
            kind = "unmeasurable"
        elif threshold and value > threshold:
            kind = "exceeded"
        else:
            kind = "within"
        buckets.setdefault(kind, []).append(payload[:60])
    total = sum(len(v) for v in buckets.values()) or 1
    return {"protocol": "error_taxonomy",
            "taxonomy": {k: {"count": len(v), "rate": round(len(v) / total, 4),
                              "examples": v[:3]} for k, v in sorted(buckets.items())}}



def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="（大模型推理场景）梯度累积与有效批量的测量噪声主要来自哪里？用路由与负载分布估计噪声水平，并求出结论仍然稳定的最小样本量。")
    ap.add_argument("--input", help="输入文件路径")
    ap.add_argument("--limit", type=int, default=0, help="只处理前 N 行")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出结果")
    ap.add_argument("--threshold", type=float, default=0.0, help="判定阈值")
    ap.add_argument("--budget", type=int, default=50, help="预算条数")
    ap.add_argument("--bins", type=int, default=10, help="分桶数量")
    ap.add_argument("--components", default="", help="组件列表（逗号分隔）")
    args = ap.parse_args(argv)

    if not args.input:
        ap.print_help()
        return 0

    t0 = time.time()
    try:
        rows = _read_rows(args.input, args.limit)
    except OSError as exc:
        print(f"读取失败：{exc}", file=sys.stderr)
        return 2

    measured = measure(rows)
    result = run_protocol(measure, rows, args)
    result["measure"] = measured
    result["row_count"] = len(rows)
    result["failure_mode"] = FAILURE_MODE
    result["elapsed_seconds"] = round(time.time() - t0, 4)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        value = measured.get(MEASURE_FIELD)
        print(f"读取 1 个文件，共 {result['row_count']} 条记录")
        print(f"{MEASURE_FIELD} = {value}")
        print(f"处理完成，耗时 {result['elapsed_seconds']}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
