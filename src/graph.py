from __future__ import annotations

import networkx as nx
import pandas as pd


def build_transaction_graph(df: pd.DataFrame) -> nx.MultiDiGraph:
    graph = nx.MultiDiGraph()

    for row in df.itertuples(index=False):
        graph.add_edge(
            str(row.from_address),
            str(row.to_address),
            key=str(row.tx_id),
            tx_id=str(row.tx_id),
            timestamp=str(row.timestamp),
            amount_btc=float(row.amount_btc),
            scenario=str(getattr(row, "risk_scenario", "") or ""),
        )

    return graph


def address_hops(
    graph: nx.MultiDiGraph, seed: str, max_hops: int = 3
) -> dict[str, int]:
    if seed not in graph:
        return {}

    return dict(
        nx.single_source_shortest_path_length(
            graph, seed, cutoff=max_hops
        )
    )


def traced_transactions(
    df: pd.DataFrame, hop_map: dict[str, int], max_hops: int
) -> pd.DataFrame:
    out = df.copy()

    def source_hop(address: str):
        return hop_map.get(str(address))

    out["source_hop"] = out["from_address"].apply(source_hop)
    traced = out[
        out["source_hop"].notna()
        & (out["source_hop"].astype(int) < max_hops)
    ].copy()

    traced["source_hop"] = traced["source_hop"].astype(int)
    return traced.sort_values(
        ["source_hop", "timestamp", "tx_id"]
    ).reset_index(drop=True)
