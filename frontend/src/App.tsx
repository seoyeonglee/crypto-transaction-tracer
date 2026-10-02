import cytoscape, { Core, ElementDefinition } from "cytoscape";
import { FormEvent, useEffect, useMemo, useRef, useState } from "react";

import { api } from "./api";
import type { Direction, MetaResponse, RiskNode, TraceCase, TraceResponse } from "./types";

function shortAddress(value: string) {
  if (value.length <= 18) return value;
  return `${value.slice(0, 8)}…${value.slice(-6)}`;
}

function severityLabel(value: string) {
  return value === "none" ? "CLEAR" : value.toUpperCase();
}

function App() {
  const graphRef = useRef<HTMLDivElement | null>(null);
  const cyRef = useRef<Core | null>(null);

  const [meta, setMeta] = useState<MetaResponse | null>(null);
  const [trace, setTrace] = useState<TraceResponse | null>(null);
  const [seed, setSeed] = useState("SEED_WALLET");
  const [hops, setHops] = useState(3);
  const [direction, setDirection] = useState<Direction>("outbound");
  const [selected, setSelected] = useState<RiskNode | null>(null);
  const [activeCase, setActiveCase] = useState("exposure-chain");
  const [loading, setLoading] = useState(true);
  const [apiState, setApiState] = useState<"checking" | "online" | "error">("checking");
  const [error, setError] = useState("");

  async function runTrace(nextSeed = seed, nextHops = hops, nextDirection = direction) {
    setLoading(true);
    setError("");
    try {
      const result = await api.trace(nextSeed, nextHops, nextDirection);
      setTrace(result);
      setSelected(result.nodes.find((node) => node.address === nextSeed) ?? result.nodes[0] ?? null);
      setApiState("online");
    } catch (err) {
      setApiState("error");
      setError(err instanceof Error ? err.message : "Trace request failed.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    (async () => {
      try {
        const nextMeta = await api.meta();
        setMeta(nextMeta);
        setApiState("online");
        await runTrace("SEED_WALLET", 3, "outbound");
      } catch (err) {
        setApiState("error");
        setError(err instanceof Error ? err.message : "API unavailable.");
        setLoading(false);
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!graphRef.current || !trace) return;

    const elements: ElementDefinition[] = [
      ...trace.nodes.map((node) => ({
        data: {
          id: node.address,
          label: shortAddress(node.address),
          fullLabel: node.address,
          severity: node.severity,
          score: node.risk_score,
          category: node.category,
          hop: node.hop,
        },
      })),
      ...trace.edges.map((edge) => ({
        data: {
          id: edge.id,
          source: edge.source,
          target: edge.target,
          amount: edge.amount_btc,
          label: `${edge.amount_btc.toFixed(3)} BTC`,
        },
      })),
    ];

    cyRef.current?.destroy();
    const cy = cytoscape({
      container: graphRef.current,
      elements,
      minZoom: 0.45,
      maxZoom: 2.4,
      wheelSensitivity: 0.22,
      style: [
        {
          selector: "node",
          style: {
            "background-color": "#132534",
            "border-width": 2,
            "border-color": "#37536a",
            label: "data(label)",
            color: "#c9d8e5",
            "font-family": "Inter, system-ui, sans-serif",
            "font-size": 9,
            "text-valign": "bottom",
            "text-margin-y": 8,
            width: 34,
            height: 34,
            "overlay-opacity": 0,
          },
        },
        {
          selector: 'node[category = "seed"]',
          style: {
            "background-color": "#0d3841",
            "border-color": "#58e6d9",
            width: 48,
            height: 48,
            color: "#82fff2",
            "font-weight": 700,
          },
        },
        {
          selector: 'node[severity = "medium"]',
          style: { "background-color": "#3a2d16", "border-color": "#f2b84b", color: "#ffd889" },
        },
        {
          selector: 'node[severity = "high"]',
          style: { "background-color": "#44201e", "border-color": "#ff756b", color: "#ffaaa4" },
        },
        {
          selector: 'node[severity = "critical"]',
          style: {
            "background-color": "#4d151d",
            "border-color": "#ff3c5f",
            color: "#ff8499",
            width: 46,
            height: 46,
            "border-width": 3,
          },
        },
        {
          selector: 'node[category = "risk_service"]',
          style: {
            shape: "diamond",
            width: 52,
            height: 52,
            "background-color": "#3f111a",
            "border-color": "#ff3c5f",
          },
        },
        {
          selector: "node:selected",
          style: {
            "border-color": "#ffffff",
            "border-width": 3,
            "underlay-color": "#58e6d9",
            "underlay-opacity": 0.17,
            "underlay-padding": 10,
          },
        },
        {
          selector: "edge",
          style: {
            width: 1.5,
            "line-color": "#30485b",
            "target-arrow-color": "#4d6a80",
            "target-arrow-shape": "triangle",
            "curve-style": "bezier",
            opacity: 0.78,
            label: "data(label)",
            color: "#6f8798",
            "font-size": 7,
            "text-background-color": "#071019",
            "text-background-opacity": 0.82,
            "text-background-padding": 2,
            "text-rotation": "autorotate",
            "overlay-opacity": 0,
          },
        },
        {
          selector: "edge:selected",
          style: {
            width: 3,
            "line-color": "#58e6d9",
            "target-arrow-color": "#58e6d9",
            opacity: 1,
          },
        },
      ] as any,
      layout: {
        name: "breadthfirst",
        directed: true,
        roots: [trace.investigation.seed],
        spacingFactor: 1.25,
        padding: 38,
        animate: false,
      },
    });

    cy.on("tap", "node", (event) => {
      const address = event.target.id();
      const node = trace.nodes.find((item) => item.address === address);
      if (node) setSelected(node);
    });

    cyRef.current = cy;
    return () => cy.destroy();
  }, [trace]);

  const selectedEdges = useMemo(() => {
    if (!trace || !selected) return [];
    return trace.edges
      .filter((edge) => edge.source === selected.address || edge.target === selected.address)
      .slice(0, 8);
  }, [trace, selected]);

  function chooseCase(item: TraceCase) {
    setActiveCase(item.id);
    setSeed(item.seed);
    setHops(item.hops);
    setDirection(item.direction);
    void runTrace(item.seed, item.hops, item.direction);
  }

  function submit(event: FormEvent) {
    event.preventDefault();
    void runTrace();
  }

  const highestPath = trace?.risk_paths[0];

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark">T//L</div>
          <div>
            <strong>TRACE//LAB</strong>
            <span>Blockchain Investigation Console</span>
          </div>
        </div>
        <div className="topbar-meta">
          <span className="classification">SYNTHETIC DATA</span>
          <span className={`api-status ${apiState}`}>
            <i /> API {apiState === "online" ? "ONLINE" : apiState === "error" ? "OFFLINE" : "CHECKING"}
          </span>
          <a href={api.baseUrl + "/docs"} target="_blank" rel="noreferrer">API DOCS ↗</a>
          <a href="https://github.com/seoyeonglee/crypto-transaction-tracer" target="_blank" rel="noreferrer">GITHUB ↗</a>
        </div>
      </header>

      <div className="workspace">
        <aside className="sidebar">
          <div className="sidebar-section">
            <div className="section-kicker">INVESTIGATION QUEUE</div>
            <h2>Case presets</h2>
            <p>Public-safe scenarios built from synthetic transaction data.</p>
          </div>

          <div className="case-list">
            {meta?.cases.map((item, index) => (
              <button
                key={item.id}
                className={`case-card ${activeCase === item.id ? "active" : ""}`}
                onClick={() => chooseCase(item)}
              >
                <span className="case-num">0{index + 1}</span>
                <span className="case-copy">
                  <strong>{item.name}</strong>
                  <small>{item.description}</small>
                </span>
                <span className="case-arrow">↗</span>
              </button>
            ))}
          </div>

          <div className="dataset-card">
            <span className="section-kicker">DATASET</span>
            <strong>{meta?.dataset.name ?? "Loading…"}</strong>
            <dl>
              <div><dt>Transactions</dt><dd>{meta?.dataset.transactions ?? "—"}</dd></div>
              <div><dt>Addresses</dt><dd>{meta?.dataset.addresses ?? "—"}</dd></div>
              <div><dt>Asset</dt><dd>BTC</dd></div>
              <div><dt>Source</dt><dd>Generated</dd></div>
            </dl>
          </div>

          <div className="disclaimer">
            <span>PUBLIC-SAFE LAB</span>
            All addresses, labels, and transaction scenarios are fictional. No real wallet attribution is performed.
          </div>
        </aside>

        <main className="main">
          <section className="trace-toolbar">
            <form onSubmit={submit} className="trace-form">
              <label>
                <span>SEED ADDRESS</span>
                <input
                  value={seed}
                  onChange={(event) => {
                    setSeed(event.target.value);
                    setActiveCase("");
                  }}
                  list="address-list"
                  placeholder="Enter synthetic address"
                />
                <datalist id="address-list">
                  {meta?.addresses.map((address) => <option key={address} value={address} />)}
                </datalist>
              </label>

              <div className="control-group">
                <span>HOPS</span>
                <div className="segmented">
                  {[1, 2, 3, 4].map((value) => (
                    <button
                      type="button"
                      key={value}
                      className={hops === value ? "on" : ""}
                      onClick={() => setHops(value)}
                    >
                      {value}
                    </button>
                  ))}
                </div>
              </div>

              <div className="control-group direction">
                <span>DIRECTION</span>
                <div className="segmented">
                  {(["outbound", "inbound", "both"] as Direction[]).map((value) => (
                    <button
                      type="button"
                      key={value}
                      className={direction === value ? "on" : ""}
                      onClick={() => setDirection(value)}
                    >
                      {value}
                    </button>
                  ))}
                </div>
              </div>

              <button className="run-button" disabled={loading}>
                {loading ? "TRACING…" : "RUN TRACE"} <span>⌁</span>
              </button>
            </form>
          </section>

          {error && <div className="error-banner">{error}</div>}

          <section className="metrics">
            <div className="metric"><span>ADDRESSES</span><strong>{trace?.summary.addresses ?? "—"}</strong><small>in current trace</small></div>
            <div className="metric"><span>TRANSACTIONS</span><strong>{trace?.summary.transactions ?? "—"}</strong><small>graph edges</small></div>
            <div className="metric"><span>FLOW VOLUME</span><strong>{trace ? trace.summary.flow_volume_btc.toFixed(3) : "—"}</strong><small>BTC in view</small></div>
            <div className="metric danger"><span>FLAGGED</span><strong>{trace?.summary.flagged_addresses ?? "—"}</strong><small>score &gt; 0</small></div>
            <div className="metric danger"><span>MAX RISK</span><strong>{trace?.summary.max_risk_score ?? "—"}</strong><small>/ 100</small></div>
          </section>

          <section className="investigation-grid">
            <div className="graph-panel panel">
              <div className="panel-head">
                <div>
                  <span className="section-kicker">TRANSACTION GRAPH</span>
                  <h2>{trace?.investigation.case_id ?? "Preparing investigation…"}</h2>
                </div>
                <div className="legend">
                  <span><i className="dot seed" />Seed</span>
                  <span><i className="dot medium" />Medium</span>
                  <span><i className="dot high" />High</span>
                  <span><i className="dot critical" />Critical</span>
                </div>
              </div>
              <div className="graph-stage">
                {loading && <div className="loading-layer"><div className="scanner" /><span>RECONSTRUCTING FLOW GRAPH</span></div>}
                <div ref={graphRef} className="cy" />
                <div className="graph-hint">Drag nodes · scroll to zoom · select an address for evidence</div>
              </div>
            </div>

            <aside className="inspector panel">
              <div className="panel-head inspector-head">
                <div>
                  <span className="section-kicker">ADDRESS INSPECTOR</span>
                  <h2>{selected ? shortAddress(selected.address) : "Select a node"}</h2>
                </div>
                {selected && <span className={`severity ${selected.severity}`}>{severityLabel(selected.severity)}</span>}
              </div>

              {selected ? (
                <>
                  <div className="risk-score">
                    <div
                      className={`score-ring ${selected.severity}`}
                      style={{ "--score": selected.risk_score } as React.CSSProperties}
                    >
                      <span>{selected.risk_score}</span>
                      <small>RISK</small>
                    </div>
                    <div className="score-copy">
                      <span>EXPLAINABLE SCORE</span>
                      <strong>{selected.synthetic_label || selected.category.replace("_", " ")}</strong>
                      <small>Hop {selected.hop} from seed · {selected.in_degree} in / {selected.out_degree} out</small>
                    </div>
                  </div>

                  <div className="address-full">{selected.address}</div>

                  <div className="rules">
                    <div className="subhead">TRIGGERED SIGNALS</div>
                    {selected.rule_explanations.length ? selected.rule_explanations.map((rule) => (
                      <div className="rule" key={rule.rule}>
                        <span>⚑</span>
                        <div><strong>{rule.rule}</strong><small>{rule.description}</small></div>
                      </div>
                    )) : <div className="clear-state">No risk rules triggered for this address.</div>}
                  </div>

                  <div className="tx-mini">
                    <div className="subhead">CONNECTED TRANSACTIONS</div>
                    {selectedEdges.map((edge) => (
                      <div className="tx-row" key={edge.id}>
                        <span>{edge.id}</span>
                        <strong>{edge.amount_btc.toFixed(4)} BTC</strong>
                        <small>{edge.source === selected.address ? "OUT" : "IN"}</small>
                      </div>
                    ))}
                  </div>
                </>
              ) : (
                <div className="empty-inspector">Select an address in the graph to inspect evidence.</div>
              )}
            </aside>
          </section>

          <section className="evidence-grid">
            <div className="panel path-panel">
              <div className="panel-head">
                <div>
                  <span className="section-kicker">EXPOSURE PATH</span>
                  <h2>{highestPath ? `${highestPath.hops}-hop path to labelled service` : "No labelled-service path in current view"}</h2>
                </div>
              </div>
              {highestPath ? (
                <div className="path-flow">
                  {highestPath.path.map((address, index) => (
                    <div className="path-step" key={address}>
                      <div className={`path-node ${address === highestPath.target ? "target" : ""}`}>
                        <span>{index === 0 ? "SEED" : index === highestPath.path.length - 1 ? "LABEL" : `HOP ${index}`}</span>
                        <strong>{shortAddress(address)}</strong>
                      </div>
                      {index < highestPath.path.length - 1 && <div className="path-arrow">→</div>}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="path-empty">Change the seed, hop depth, or direction to investigate a different flow.</div>
              )}
            </div>

            <div className="panel analyst-panel">
              <div className="panel-head">
                <div>
                  <span className="section-kicker">ANALYST NOTE</span>
                  <h2>Interpretation guardrails</h2>
                </div>
              </div>
              <p>
                Graph structure and proximity are investigative signals, not attribution.
                Fan-in, fan-out, and peel-like patterns can have legitimate explanations.
                Escalation should combine transaction context, service labels, temporal behavior,
                counterparties, and external evidence.
              </p>
              <div className="guardrails">
                <span>✓ Traceable rules</span>
                <span>✓ Synthetic labels</span>
                <span>✓ No black-box attribution</span>
              </div>
            </div>
          </section>

          <section className="panel transaction-panel">
            <div className="panel-head">
              <div>
                <span className="section-kicker">TRACE EVIDENCE</span>
                <h2>Transactions in current investigation</h2>
              </div>
              <span className="rows-count">{trace?.edges.length ?? 0} ROWS</span>
            </div>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr><th>TX ID</th><th>TIME</th><th>FROM</th><th>TO</th><th>AMOUNT</th><th>SCENARIO</th></tr>
                </thead>
                <tbody>
                  {trace?.edges.map((edge) => (
                    <tr key={edge.id}>
                      <td className="mono accent">{edge.id}</td>
                      <td className="mono">{edge.timestamp.replace("T", " ")}</td>
                      <td className="mono">{shortAddress(edge.source)}</td>
                      <td className="mono">{shortAddress(edge.target)}</td>
                      <td className="mono amount">{edge.amount_btc.toFixed(8)} BTC</td>
                      <td><span className="scenario">{edge.scenario || "ordinary_transfer"}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </main>
      </div>
    </div>
  );
}

export default App;
