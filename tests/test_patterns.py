import pandas as pd

from src.graph import build_transaction_graph
from src.patterns import address_risk_table, structural_flags


def row(tx_id, source, target):
    return {
        "tx_id": tx_id,
        "timestamp": "2026-09-01T10:00:00",
        "from_address": source,
        "to_address": target,
        "amount_btc": 0.1,
        "asset": "BTC",
        "risk_scenario": "",
    }


def test_fan_out_detection():
    df = pd.DataFrame([
        row(f"T{i}", "HUB", f"O{i}")
        for i in range(6)
    ])
    graph = build_transaction_graph(df)
    flags = structural_flags(graph)
    assert "FAN_OUT" in flags["HUB"]


def test_risk_proximity():
    df = pd.DataFrame([
        row("T1", "A", "B"),
        row("T2", "B", "SYNTH_MIXER"),
    ])
    graph = build_transaction_graph(df)
    risks = address_risk_table(graph)

    b = risks[risks["address"] == "B"].iloc[0]
    mixer = risks[risks["address"] == "SYNTH_MIXER"].iloc[0]

    assert "ONE_HOP_RISK_EXPOSURE" in b["rules"]
    assert "DIRECT_RISK_LABEL" in mixer["rules"]
