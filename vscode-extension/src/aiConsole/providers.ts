import * as fs from "fs";
import * as path from "path";

import {
  AgentRegistryConfig,
  SonaAgent,
  SonaAgentId,
  getAgents
} from "./agentRegistry";

export interface AgentContext {
  currentFile?: string;
  selection?: string;
  diagnostics?: unknown[];
  workspaceName?: string;
  languageId?: string;
}

export interface AgentRequest {
  agentId: SonaAgentId;
  prompt: string;
  context: AgentContext;
}

export interface AgentResponse {
  agentId: SonaAgentId;
  text: string;
  status: "ok" | "not_configured" | "error";
}

export interface DeveloperIntelligenceTransport {
  execute(request: AgentRequest, providerId?: string): Promise<AgentResponse>;
}

export interface ProviderConfig {
  qwenEnabled: boolean;
  qwenModel: string;
  ollamaUrl: string;
  claudeEnabled: boolean;
  codexEnabled: boolean;
  workspaceFolderPaths: string[];
  timeoutMs?: number;
  transport?: DeveloperIntelligenceTransport;
}

export interface ProviderStatus {
  agents: SonaAgent[];
  qwen: {
    configured: boolean;
    model?: string;
    url?: string;
    source?: string;
  };
  claude: {
    configured: boolean;
    reason: string;
  };
  codex: {
    configured: boolean;
    reason: string;
  };
}

interface OllamaConfig {
  configured: boolean;
  model?: string;
  url?: string;
  source?: string;
  reason?: string;
}

const DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434";
const DEFAULT_QWEN_MODEL = "qwen2.5-coder:7b";

export function getProviderStatus(config: ProviderConfig): ProviderStatus {
  const qwen = resolveQwenConfig(config);
  const registryConfig: AgentRegistryConfig = {
    qwenConfigured: qwen.configured,
    claudeConfigured: false,
    codexConfigured: false
  };

  return {
    agents: getAgents(registryConfig),
    qwen: {
      configured: qwen.configured,
      model: qwen.model,
      url: qwen.url,
      source: qwen.source
    },
    claude: {
      configured: false,
      reason: "Claude provider is not configured yet."
    },
    codex: {
      configured: false,
      reason: "Codex provider is not configured yet."
    }
  };
}

export async function routeAgentRequest(
  request: AgentRequest,
  config: ProviderConfig
): Promise<AgentResponse> {
  try {
    if (!config.transport) {
      return {
        agentId: request.agentId,
        status: "error",
        text: "The governed Sona backend transport is unavailable."
      };
    }
    const provider = request.agentId === "qwen" ? "ollama"
      : request.agentId === "claude" ? "claude"
      : request.agentId === "codex" ? "codex"
      : undefined;
    return config.transport.execute(request, provider);
  } catch (error) {
    return {
      agentId: request.agentId,
      status: "error",
      text: error instanceof Error ? error.message : String(error)
    };
  }
}

export function resolveQwenConfig(config: ProviderConfig): OllamaConfig {
  const explicitModel = clean(config.qwenModel) || DEFAULT_QWEN_MODEL;
  const explicitUrl = clean(config.ollamaUrl) || DEFAULT_OLLAMA_URL;

  if (config.qwenEnabled) {
    return {
      configured: true,
      model: explicitModel,
      url: normalizeOllamaUrl(explicitUrl),
      source: "settings"
    };
  }

  const envConfig = readWorkspaceOllamaEnv(config.workspaceFolderPaths);
  if (envConfig && isQwenModel(envConfig.model)) {
    return {
      configured: true,
      model: envConfig.model,
      url: normalizeOllamaUrl(envConfig.url || explicitUrl),
      source: ".env"
    };
  }

  return {
    configured: false,
    model: explicitModel,
    url: normalizeOllamaUrl(explicitUrl),
    reason: "Qwen is not enabled and no workspace Ollama/Qwen .env configuration was found."
  };
}

function readWorkspaceOllamaEnv(workspaceFolderPaths: string[]): { model: string; url?: string } | undefined {
  for (const folder of workspaceFolderPaths) {
    const envPath = path.join(folder, ".env");
    if (!fs.existsSync(envPath)) {
      continue;
    }
    const parsed = parseDotenv(fs.readFileSync(envPath, "utf8"));
    const backend = clean(parsed.SONA_AI_BACKEND || parsed.SONA_AI_PROVIDER);
    const model = clean(parsed.SONA_OLLAMA_MODEL);
    if (backend && backend.toLowerCase() === "ollama" && model) {
      return {
        model,
        url: clean(parsed.OLLAMA_HOST)
      };
    }
  }
  return undefined;
}

function parseDotenv(content: string): Record<string, string> {
  const parsed: Record<string, string> = {};
  for (const rawLine of content.split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line || line.startsWith("#") || !line.includes("=")) {
      continue;
    }
    const [rawKey, ...rawValue] = line.split("=");
    const key = rawKey.trim();
    let value = rawValue.join("=").trim();
    if ((value.startsWith("\"") && value.endsWith("\"")) || (value.startsWith("'") && value.endsWith("'"))) {
      value = value.slice(1, -1);
    }
    if (key) {
      parsed[key] = value;
    }
  }
  return parsed;
}

function isQwenModel(model: string | undefined): boolean {
  return Boolean(model && model.toLowerCase().includes("qwen"));
}

function normalizeOllamaUrl(url: string): string {
  const trimmed = clean(url) || DEFAULT_OLLAMA_URL;
  const withProtocol = /^https?:\/\//i.test(trimmed) ? trimmed : `http://${trimmed}`;
  return withProtocol.replace(/\/+$/, "");
}

function clean(value: string | undefined): string | undefined {
  const trimmed = (value || "").trim();
  return trimmed || undefined;
}
