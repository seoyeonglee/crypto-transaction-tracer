from __future__ import annotations

from collections import Counter

import networkx as nx
import pandas as pd


SYNTHETIC_RISK_LABELS = {
    "SYNTH_MIXER": "synthetic_mixer",
    "SYNTH_HIGH_RISK_SERVICE": "synthetic_high_risk_service",
}

RISK_WEIGHTS = {
    "DIRECT_RISK_LABEL": 60,
    "ONE_HOP_RISK_EXPOSURE": 40,
    "TWO_HOP_RISK_EXPOSURE": 20,
    "FAN_OUT": 25,
    "FAN_IN": 20,
    "PEEL_CHAIN": 25,
}


def structural_flags(graph: nx.MultiDiGraph) -> dict[str, list[str]]:
    flags: dict[str, list[str]] = {node: [] for node in graph.nodes}

    for node in graph.nodes:
        if graph.out_degree(node) >= 5:
            flags[node].append("FAN_OUT")
        if graph.in_degree(node) >= 5:
            flags[node].append("FAN_IN")

    # Simplified peel-chain heuristic:
    # a sequence of addresses with exactly two outgoing destinations,
    # one of which continues the chain.
    for node in graph.nodes:
        successors = list(dict.fromkeys(graph.successors(node)))
        if len(successors) != 2:
            continue

        continuing = [
            nxt
            for nxt in successors
            if graph.out_degree(nxt) >= 1
        ]
        if continuing:
            flags[node].append("PEEL_CHAIN")

    return flags


def risk_distance_to_labels(
    graph: nx.MultiDiGraph,
    labels: dict[str, str] | None = None,
    max_distance: int = 2,
) -> dict[str, int | None]:
    labels = labels or SYNTHETIC_RISK_LABELS
    reversed_graph = graph.reverse(copy=False)
    result: dict[str, int | None] = {
        node: None for node in graph.nodes
    }

    for risky in labels:
        if risky not in graph:
            continue

        distances = nx.single_source_shortest_path_length(
            reversed_graph, risky, cutoff=max_distance
        )
        for node, distance in distances.items():
            current = result.get(node)
            if current is None or distance < current:
                result[node] = int(distance)

    return result


def address_risk_table(
    graph: nx.MultiDiGraph,
    labels: dict[str, str] | None = None,
) -> pd.DataFrame:
    labels = labels or SYNTHETIC_RISK_LABELS
    flags = structural_flags(graph)
    distances = risk_distance_to_labels(graph, labels)

    rows = []
    for node in sorted(graph.nodes):
        rules = list(flags.get(node, []))
        distance = distances.get(node)

        if node in labels:
            rules.append("DIRECT_RISK_LABEL")
        elif distance == 1:
            rules.append("ONE_HOP_RISK_EXPOSURE")
        elif distance == 2:
            rules.append("TWO_HOP_RISK_EXPOSURE")

        score = min(
            100,
            sum(RISK_WEIGHTS.get(rule, 0) for rule in rules),
        )

        if score >= 80:
            severity = "critical"
        elif score >= 60:
            severity = "high"
        elif score >= 30:
            severity = "medium"
        elif score > 0:
            severity = "low"
        else:
            severity = "none"

        rows.append({
            "address": node,
            "in_degree": int(graph.in_degree(node)),
            "out_degree": int(graph.out_degree(node)),
            "risk_distance": distance,
            "synthetic_label": labels.get(node, ""),
            "rules": rules,
            "risk_score": score,
            "severity": severity,
        })

    return pd.DataFrame(rows).sort_values(
        ["risk_score", "address"], ascending=[False, True]
    ).reset_index(drop=True)
