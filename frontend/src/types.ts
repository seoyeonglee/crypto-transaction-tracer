export type Direction = "outbound" | "inbound" | "both";

export type TraceCase = {
  id: string;
  name: string;
  seed: string;
  hops: number;
  direction: Direction;
  description: string;
  analyst_note: string;
};

export type RiskRule = {
  rule: string;
  description: string;
};

export type RiskNode = {
  address: string;
  in_degree: number;
  out_degree: number;
  risk_distance: number | null;
  synthetic_label: string;
  rules: string[];
  risk_score: number;
  severity: "critical" | "high" | "medium" | "low" | "none";
  hop: number;
  category: string;
  rule_explanations: RiskRule[];
};

export type TraceEdge = {
  id: string;
  source: string;
  target: string;
  timestamp: string;
  amount_btc: number;
  asset: string;
  scenario: string;
};

export type RiskPath = {
  target: string;
  label: string;
  hops: number;
  path: string[];
};

export type TraceResponse = {
  investigation: {
    case_id: string;
    seed: string;
    max_hops: number;
    direction: Direction;
    data_classification: string;
  };
  summary: {
    addresses: number;
    transactions: number;
    flow_volume_btc: number;
    flagged_addresses: number;
    high_or_critical: number;
    max_risk_score: number;
  };
  nodes: RiskNode[];
  edges: TraceEdge[];
  risk_paths: RiskPath[];
  note: string;
};

export type MetaResponse = {
  dataset: {
    name: string;
    transactions: number;
    addresses: number;
    asset: string;
    synthetic: boolean;
  };
  cases: TraceCase[];
  addresses: string[];
  top_risk: RiskNode[];
};
