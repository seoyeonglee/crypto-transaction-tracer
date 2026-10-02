from __future__ import annotations

from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Literal

import networkx as nx
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.graph import build_transaction_graph
from src.patterns import SYNTHETIC_RISK_LABELS, address_risk_table

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "sample_transactions.csv"


class TraceCase(BaseModel):
    id: str
    name: str
    seed: str
    hops: int
    direction: Literal["outbound", "inbound", "both"]
    description: str
    analyst_note: str


CASES = [
    TraceCase(
        id="exposure-chain",
        name="Exposure Chain",
        seed="SEED_WALLET",
        hops=3,
        direction="outbound",
        description="Follow a seeded transfer through a bridge-like wallet into fan-out activity and synthetic high-risk services.",
        analyst_note="Investigate whether the fan-out is ordinary dispersal or a layering pattern with proximity to labelled services.",
    ),
    TraceCase(
        id="peel-chain",
        name="Peel Chain",
        seed="PEEL_0",
        hops=4,
        direction="outbound",
        description="Trace a repeated two-output pattern where value continues through a chain while smaller change outputs peel away.",
        analyst_note="Look for repeated continuation/change behavior rather than relying on a single transaction.",
    ),
    TraceCase(
        id="collector",
        name="Collector Fan-In",
        seed="COLLECTOR",
        hops=2,
        direction="inbound",
        description="Work backwards from a collector wallet receiving multiple inbound transfers from distinct sources.",
        analyst_note="Fan-in can be benign. Treat the pattern as an investigative lead, not attribution.",
    ),
]


@lru_cache(maxsize=1)
def load_state():
    df = pd.read_csv(DATA_PATH)
    graph = build_transaction_graph(df)
    risks = address_risk_table(graph)
    risk_by_address = {
        row.address: {
            "address": row.address,
            "in_degree": int(row.in_degree),
            "out_degree": int(row.out_degree),
            "risk_distance": None if pd.isna(row.risk_distance) else int(row.risk_distance),
            "synthetic_label": row.synthetic_label or "",
            "rules": list(row.rules),
            "risk_score": int(row.risk_score),
            "severity": row.severity,
        }
        for row in risks.itertuples(index=False)
    }
    return df, graph, risk_by_address


def category(address: str) -> str:
    if address in SYNTHETIC_RISK_LABELS:
        return "risk_service"
    if address == "SEED_WALLET":
        return "seed"
    if address.startswith("BRIDGE"):
        return "bridge"
    if address.startswith("FANOUT"):
        return "fanout"
    if address == "COLLECTOR":
        return "collector"
    if address.startswith("PEEL"):
        return "peel"
    if address.startswith("CHANGE"):
        return "change"
    if address.startswith("MERCHANT"):
        return "merchant"
    if address.startswith("SOURCE"):
        return "source"
    if address.startswith("WALLET"):
        return "wallet"
    return "unknown"


def hop_map(
    graph: nx.MultiDiGraph,
    seed: str,
    max_hops: int,
    direction: str,
) -> dict[str, int]:
    if seed not in graph:
        return {}

    if direction == "outbound":
        return dict(nx.single_source_shortest_path_length(graph, seed, cutoff=max_hops))
    if direction == "inbound":
        return dict(nx.single_source_shortest_path_length(graph.reverse(copy=False), seed, cutoff=max_hops))

    outbound = dict(nx.single_source_shortest_path_length(graph, seed, cutoff=max_hops))
    inbound = dict(nx.single_source_shortest_path_length(graph.reverse(copy=False), seed, cutoff=max_hops))
    merged = dict(outbound)
    for address, hops in inbound.items():
        merged[address] = min(merged.get(address, hops), hops)
    return merged


def explain_rule(rule: str) -> str:
    return {
        "DIRECT_RISK_LABEL": "Address carries a synthetic high-risk service label.",
        "ONE_HOP_RISK_EXPOSURE": "One transaction hop from a synthetic high-risk labelled service.",
        "TWO_HOP_RISK_EXPOSURE": "Two transaction hops from a synthetic high-risk labelled service.",
        "FAN_OUT": "Five or more outgoing edges create a fan-out pattern.",
        "FAN_IN": "Five or more incoming edges create a fan-in pattern.",
        "PEEL_CHAIN": "Two-output continuation pattern matches the simplified peel-chain heuristic.",
    }.get(rule, "Rule matched by the explainable risk engine.")


def risk_paths(graph: nx.MultiDiGraph, seed: str, nodes: set[str], direction: str):
    paths = []
    candidates = [addr for addr in SYNTHETIC_RISK_LABELS if addr in nodes]
    if direction == "inbound":
        return paths
    for target in candidates:
        try:
            path = nx.shortest_path(graph, seed, target)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            continue
        if all(node in nodes for node in path):
            paths.append(
                {
                    "target": target,
                    "label": SYNTHETIC_RISK_LABELS[target],
                    "hops": len(path) - 1,
                    "path": path,
                }
            )
    return sorted(paths, key=lambda item: item["hops"])


app = FastAPI(
    title="Crypto Transaction Tracer API",
    version="2.0.0",
    description=(
        "Synthetic blockchain-investigation API powering the public live demo. "
        "All addresses, transactions, labels, and scenarios are fictional."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "service": "crypto-transaction-tracer",
        "status": "ok",
        "docs": "/docs",
        "data": "synthetic-only",
    }


@app.get("/health")
def health():
    df, graph, _ = load_state()
    return {
        "status": "ok",
        "transactions": len(df),
        "addresses": graph.number_of_nodes(),
    }


@app.get("/api/v1/meta")
def meta():
    df, graph, risk_by_address = load_state()
    ranked = sorted(
        risk_by_address.values(),
        key=lambda item: (-item["risk_score"], item["address"]),
    )
    return {
        "dataset": {
            "name": "Synthetic BTC Investigation Lab",
            "transactions": int(len(df)),
            "addresses": int(graph.number_of_nodes()),
            "asset": "BTC",
            "synthetic": True,
        },
        "cases": [case.model_dump() for case in CASES],
        "addresses": sorted(graph.nodes),
        "top_risk": ranked[:8],
    }


@app.get("/api/v1/trace")
def trace(
    seed: str = Query(default="SEED_WALLET"),
    max_hops: int = Query(default=3, ge=1, le=5),
    direction: Literal["outbound", "inbound", "both"] = Query(default="outbound"),
):
    df, graph, risk_by_address = load_state()

    if seed not in graph:
        raise HTTPException(status_code=404, detail=f"Unknown synthetic address: {seed}")

    hops = hop_map(graph, seed, max_hops, direction)
    selected = set(hops)

    nodes = []
    for address in sorted(selected, key=lambda item: (hops[item], item)):
        risk = risk_by_address[address]
        nodes.append(
            {
                **risk,
                "hop": hops[address],
                "category": category(address),
                "rule_explanations": [
                    {"rule": rule, "description": explain_rule(rule)}
                    for rule in risk["rules"]
                ],
            }
        )

    edges = []
    for row in df.itertuples(index=False):
        source = str(row.from_address)
        target = str(row.to_address)
        if source in selected and target in selected:
            edges.append(
                {
                    "id": str(row.tx_id),
                    "source": source,
                    "target": target,
                    "timestamp": str(row.timestamp),
                    "amount_btc": float(row.amount_btc),
                    "asset": str(row.asset),
                    "scenario": str(row.risk_scenario or ""),
                }
            )

    volume = round(sum(edge["amount_btc"] for edge in edges), 8)
    flagged = [node for node in nodes if node["risk_score"] > 0]
    severities = Counter(node["severity"] for node in nodes)

    return {
        "investigation": {
            "case_id": f"TRACE-{seed}-{max_hops}-{direction}".upper(),
            "seed": seed,
            "max_hops": max_hops,
            "direction": direction,
            "data_classification": "SYNTHETIC / PUBLIC-SAFE",
        },
        "summary": {
            "addresses": len(nodes),
            "transactions": len(edges),
            "flow_volume_btc": volume,
            "flagged_addresses": len(flagged),
            "high_or_critical": severities.get("high", 0) + severities.get("critical", 0),
            "max_risk_score": max((node["risk_score"] for node in nodes), default=0),
        },
        "nodes": nodes,
        "edges": edges,
        "risk_paths": risk_paths(graph, seed, selected, direction),
        "note": "All addresses, labels, and transaction scenarios are synthetic.",
    }


@app.get("/api/v1/address/{address}")
def address_detail(address: str):
    df, graph, risk_by_address = load_state()
    if address not in graph:
        raise HTTPException(status_code=404, detail="Unknown synthetic address")

    risk = risk_by_address[address]
    inbound = df[df["to_address"].astype(str) == address].to_dict(orient="records")
    outbound = df[df["from_address"].astype(str) == address].to_dict(orient="records")

    return {
        **risk,
        "category": category(address),
        "rule_explanations": [
            {"rule": rule, "description": explain_rule(rule)}
            for rule in risk["rules"]
        ],
        "inbound_transactions": inbound,
        "outbound_transactions": outbound,
        "counterparties": sorted(
            set(graph.predecessors(address)).union(set(graph.successors(address)))
        ),
    }
