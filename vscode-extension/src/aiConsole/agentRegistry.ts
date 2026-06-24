export type SonaAgentId = "sona" | "qwen" | "claude" | "codex" | "local";

export interface SonaAgent {
  id: SonaAgentId;
  label: string;
  description: string;
  configured: boolean;
  localOnly: boolean;
}

export interface AgentRegistryConfig {
  qwenConfigured?: boolean;
  claudeConfigured?: boolean;
  codexConfigured?: boolean;
}

const AGENT_DEFINITIONS: Array<Omit<SonaAgent, "configured">> = [
  {
    id: "sona",
    label: "Sona",
    description: "Local deterministic Sona assistant. No network calls.",
    localOnly: true
  },
  {
    id: "qwen",
    label: "Qwen",
    description: "Provider-ready Qwen mode backed by configured local Ollama.",
    localOnly: true
  },
  {
    id: "claude",
    label: "Claude",
    description: "Placeholder for a future Claude provider.",
    localOnly: false
  },
  {
    id: "codex",
    label: "Codex",
    description: "Placeholder for a future Codex provider. Does not control external extensions.",
    localOnly: false
  },
  {
    id: "local",
    label: "Local",
    description: "Local deterministic assistant. No network calls.",
    localOnly: true
  }
];

export const ALL_AGENT_IDS: SonaAgentId[] = AGENT_DEFINITIONS.map(agent => agent.id);

export function isSonaAgentId(value: unknown): value is SonaAgentId {
  return typeof value === "string" && ALL_AGENT_IDS.includes(value as SonaAgentId);
}

export function normalizeAgentId(value: unknown, fallback: SonaAgentId = "sona"): SonaAgentId {
  return isSonaAgentId(value) ? value : fallback;
}

export function getAgents(config: AgentRegistryConfig = {}): SonaAgent[] {
  return AGENT_DEFINITIONS.map(agent => ({
    ...agent,
    configured: isAgentConfigured(agent.id, config)
  }));
}

export function getAgent(id: SonaAgentId, config: AgentRegistryConfig = {}): SonaAgent {
  const agent = getAgents(config).find(candidate => candidate.id === id);
  if (!agent) {
    throw new Error(`Unknown Sona agent: ${id}`);
  }
  return agent;
}

function isAgentConfigured(id: SonaAgentId, config: AgentRegistryConfig): boolean {
  if (id === "sona" || id === "local") {
    return true;
  }
  if (id === "qwen") {
    return Boolean(config.qwenConfigured);
  }
  if (id === "claude") {
    return Boolean(config.claudeConfigured);
  }
  if (id === "codex") {
    return Boolean(config.codexConfigured);
  }
  return false;
}
