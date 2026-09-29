from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

try:
    from .graph import address_hops, build_transaction_graph, traced_transactions
    from .patterns import address_risk_table
except ImportError:
    from graph import address_hops, build_transaction_graph, traced_transactions
    from patterns import address_risk_table


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/sample_transactions.csv")
    parser.add_argument("--seed-address", default="SEED_WALLET")
    parser.add_argument("--max-hops", type=int, default=3)
    parser.add_argument("--trace-output", default="output/traced_transactions.csv")
    parser.add_argument("--risk-output", default="output/address_risk.csv")
    parser.add_argument("--summary", default="output/summary.json")
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    graph = build_transaction_graph(df)
    hops = address_hops(graph, args.seed_address, args.max_hops)
    traced = traced_transactions(df, hops, args.max_hops)
    risks = address_risk_table(graph)

    Path(args.trace_output).parent.mkdir(parents=True, exist_ok=True)
    traced.to_csv(args.trace_output, index=False)

    risk_out = risks.copy()
    risk_out["rules"] = risk_out["rules"].apply(lambda x: "|".join(x))
    risk_out.to_csv(args.risk_output, index=False)

    summary = {
        "seed_address": args.seed_address,
        "max_hops": args.max_hops,
        "transactions_loaded": int(len(df)),
        "addresses_loaded": int(graph.number_of_nodes()),
        "traced_addresses": int(len(hops)),
        "traced_transactions": int(len(traced)),
        "medium_or_higher_risk_addresses": int((risks["risk_score"] >= 30).sum()),
        "note": "All addresses and risk labels in this repository are synthetic.",
    }
    Path(args.summary).write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
