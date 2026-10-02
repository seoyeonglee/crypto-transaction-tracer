# Crypto Transaction Tracer

[![tests](https://github.com/seoyeonglee/crypto-transaction-tracer/actions/workflows/tests.yml/badge.svg)](https://github.com/seoyeonglee/crypto-transaction-tracer/actions/workflows/tests.yml)
[![Live Demo](https://img.shields.io/badge/Live_Demo-Trace%2F%2FLab-58E6D9)](https://seoyoung-crypto-tracer.onrender.com)
[![API Docs](https://img.shields.io/badge/API-FastAPI-009688)](https://seoyoung-crypto-tracer-api.onrender.com/docs)

**[Open Live Investigation Console](https://seoyoung-crypto-tracer.onrender.com)** · **[Open Swagger API](https://seoyoung-crypto-tracer-api.onrender.com/docs)**

**Interactive blockchain-investigation lab with graph tracing, explainable risk signals, and an analyst-style web console.**

> All addresses, transactions, labels, and scenarios in this repository are fictional. The project does not contain real wallet data, sanctioned-address lists, customer information, or employer investigation logic.

## Live investigation console

[![Trace//Lab live investigation console](docs/live-console.png)](https://seoyoung-crypto-tracer.onrender.com)

The deployed console is designed to feel like an analyst workstation rather than a generic portfolio dashboard:

- choose a synthetic investigation case or seed address;
- switch outbound / inbound / bidirectional tracing;
- change hop depth and rebuild the graph;
- inspect addresses, transaction volume, proximity, and explainable risk signals;
- follow exposure paths to synthetic labelled services;
- review the exact transactions supporting the current graph.

The UI talks to the same FastAPI/NetworkX analysis layer that powers the repository's tracing logic. Render free-tier services may cold-start after inactivity.

## What this project demonstrates

- React + TypeScript investigation console
- interactive transaction-graph visualization with Cytoscape.js
- FastAPI backend built on the existing Python/NetworkX tracing engine
- outbound, inbound, and bidirectional hop tracing
- explainable fan-in, fan-out, peel-chain, and risk-proximity signals
- analyst-facing evidence panels rather than opaque scoring
- synthetic case presets for exposure chains, peel chains, and collectors
- Docker Compose local full-stack execution
- backend tests + frontend production build in GitHub Actions

## Architecture

```mermaid
flowchart LR
    UI[React / TypeScript Console] --> API[FastAPI]
    API --> G[NetworkX MultiDiGraph]
    API --> R[Explainable Risk Engine]
    D[Synthetic BTC Transactions] --> G
    G --> T[Hop Trace]
    G --> R
    T --> UI
    R --> UI
```

## Live-demo interaction model

The UI is deliberately styled like an investigation product rather than a generic dashboard:

1. pick an investigation case or seed address;
2. choose hop depth and trace direction;
3. reconstruct the transaction graph;
4. select an address to inspect its score, signals, and connected transactions;
5. review the shortest visible exposure path to a synthetic labelled service;
6. inspect the evidence table supporting the graph.

## Existing tracing engine

The original CLI and reproducible outputs remain intact:

```bash
python src/generate_data.py
python src/run_trace.py --seed-address SEED_WALLET --max-hops 3
pytest -q
```

## Run the live app locally

```bash
docker compose up --build
```

Then open:

- Frontend: `http://localhost:5173`
- API docs: `http://localhost:8000/docs`

## Design principles

- **Synthetic by design** — no real operational targets
- **Explainable** — every score is tied to visible graph signals
- **Investigation-oriented** — patterns are leads, not attribution
- **Reproducible** — deterministic sample generation and automated tests
- **Product-shaped** — browser UI, API boundary, interaction states, and analyst evidence flow

## Tech

React · TypeScript · Cytoscape.js · FastAPI · Python · Pandas · NetworkX · Docker · GitHub Actions
