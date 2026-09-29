import pandas as pd

from src.graph import address_hops, build_transaction_graph, traced_transactions


def test_hop_trace():
    df = pd.DataFrame([
        {"tx_id": "T1", "timestamp": "2026-09-01T10:00:00", "from_address": "A", "to_address": "B", "amount_btc": 1.0, "asset": "BTC", "risk_scenario": ""},
        {"tx_id": "T2", "timestamp": "2026-09-01T10:01:00", "from_address": "B", "to_address": "C", "amount_btc": 0.8, "asset": "BTC", "risk_scenario": ""},
        {"tx_id": "T3", "timestamp": "2026-09-01T10:02:00", "from_address": "C", "to_address": "D", "amount_btc": 0.7, "asset": "BTC", "risk_scenario": ""},
    ])

    graph = build_transaction_graph(df)
    hops = address_hops(graph, "A", 2)

    assert hops["A"] == 0
    assert hops["B"] == 1
    assert hops["C"] == 2
    assert "D" not in hops

    traced = traced_transactions(df, hops, 2)
    assert set(traced["tx_id"]) == {"T1", "T2"}
