from __future__ import annotations

import argparse
import random
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd


def tx(
    tx_id: str,
    timestamp: datetime,
    source: str,
    target: str,
    amount: float,
    scenario: str = "",
) -> dict:
    return {
        "tx_id": tx_id,
        "timestamp": timestamp.isoformat(),
        "from_address": source,
        "to_address": target,
        "amount_btc": round(amount, 8),
        "asset": "BTC",
        "risk_scenario": scenario,
    }


def generate(seed: int = 42) -> pd.DataFrame:
    rng = random.Random(seed)
    base = datetime(2026, 9, 1, 10, 0, 0)
    rows = []
    n = 1

    # Ordinary synthetic transfers.
    for i in range(30):
        source = f"WALLET_{(i % 10) + 1:02d}"
        target = f"MERCHANT_{(i % 8) + 1:02d}"
        rows.append(
            tx(
                f"TX{n:04d}",
                base + timedelta(hours=i * 3),
                source,
                target,
                rng.uniform(0.01, 0.25),
            )
        )
        n += 1

    # Trace scenario: seed -> bridge -> fan-out -> synthetic mixer.
    rows.append(tx(f"TX{n:04d}", base + timedelta(days=5), "SEED_WALLET", "BRIDGE_A", 1.8, "seed_trace")); n += 1
    for i in range(6):
        target = f"FANOUT_{i+1}"
        rows.append(tx(f"TX{n:04d}", base + timedelta(days=5, minutes=i+1), "BRIDGE_A", target, 0.25, "fan_out")); n += 1

    rows.append(tx(f"TX{n:04d}", base + timedelta(days=5, minutes=10), "FANOUT_1", "SYNTH_MIXER", 0.20, "mixer_exposure")); n += 1
    rows.append(tx(f"TX{n:04d}", base + timedelta(days=5, minutes=12), "FANOUT_2", "SYNTH_HIGH_RISK_SERVICE", 0.18, "high_risk_service_exposure")); n += 1

    # Synthetic fan-in.
    for i in range(6):
        rows.append(tx(f"TX{n:04d}", base + timedelta(days=7, minutes=i), f"SOURCE_{i+1}", "COLLECTOR", 0.04 + i * 0.005, "fan_in")); n += 1

    # Simplified peel chain.
    previous = "PEEL_0"
    for i in range(1, 5):
        continuation = f"PEEL_{i}"
        change = f"CHANGE_{i}"
        rows.append(tx(f"TX{n:04d}", base + timedelta(days=9, minutes=i*2), previous, continuation, 0.8 - i * 0.1, "peel_chain")); n += 1
        rows.append(tx(f"TX{n:04d}", base + timedelta(days=9, minutes=i*2+1), previous, change, 0.05, "peel_chain")); n += 1
        previous = continuation

    return pd.DataFrame(rows).sort_values("timestamp").reset_index(drop=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="data/sample_transactions.csv")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    df = generate(args.seed)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output, index=False)
    print(f"Wrote {len(df)} synthetic blockchain transactions to {output}")


if __name__ == "__main__":
    main()
