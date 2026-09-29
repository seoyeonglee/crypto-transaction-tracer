# Methodology

This is a synthetic blockchain-investigation project. All addresses, transactions, labels, and scenarios are fictional.

## Investigation model

The transaction ledger is represented as a directed multi-graph:

- nodes = addresses
- edges = transactions
- edge attributes = transaction ID, timestamp, amount, scenario label

A seed address can be traced outward for a configurable number of hops.

## Risk signals

| Signal | Meaning | Weight |
|---|---|---:|
| `DIRECT_RISK_LABEL` | Synthetic labeled service address | 60 |
| `ONE_HOP_RISK_EXPOSURE` | One edge from a labeled address | 40 |
| `TWO_HOP_RISK_EXPOSURE` | Two edges from a labeled address | 20 |
| `FAN_OUT` | Five or more outgoing transactions | 25 |
| `FAN_IN` | Five or more incoming transactions | 20 |
| `PEEL_CHAIN` | Simplified two-output continuation pattern | 25 |

## Important limitations

These are illustrative heuristics, not attribution claims. Real blockchain investigations require:

- chain-specific transaction semantics
- entity clustering controls
- change-address heuristics
- external attribution data
- temporal analysis
- exchange/service metadata
- false-positive review
- legal and evidentiary controls

The project intentionally avoids real sanctioned addresses or operational tracing targets.
