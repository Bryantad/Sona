import * as fs from "fs";
import * as http from "http";
import * as https from "https";
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

export interface ProviderConfig {
  qwenEnabled: boolean;
  qwenModel: string;
  ollamaUrl: string;
  claudeEnabled: boolean;
  codexEnabled: boolean;
  workspaceFolderPaths: string[];
  timeoutMs?: number;
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
const MAX_SELECTION_CHARS = 1200;
const MAX_PROMPT_CHARS = 1000;

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
    switch (request.agentId) {
      case "sona":
        return {
          agentId: request.agentId,
          status: "ok",
          text: buildDeterministicLocalResponse("Sona", request)
        };
      case "local":
        return {
          agentId: request.agentId,
          status: "ok",
          text: buildDeterministicLocalResponse("Local", request)
        };
      case "qwen":
        return routeQwenRequest(request, config);
      case "claude":
        return notConfigured(request.agentId, "Claude provider is not configured yet. Add configuration before using this agent.");
      case "codex":
        return notConfigured(request.agentId, "Codex provider is not configured yet. This console does not control external Codex extensions.");
      default:
        return {
          agentId: request.agentId,
          status: "error",
          text: "Unknown Sona AI Console agent."
        };
    }
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

function notConfigured(agentId: SonaAgentId, text: string): AgentResponse {
  return {
    agentId,
    status: "not_configured",
    text
  };
}

async function routeQwenRequest(
  request: AgentRequest,
  config: ProviderConfig
): Promise<AgentResponse> {
  const qwen = resolveQwenConfig(config);
  if (!qwen.configured || !qwen.model || !qwen.url) {
    return notConfigured(
      "qwen",
      "Qwen provider is not configured yet. Enable sona.ai.qwen.enabled or run Sona manual setup with a local Qwen/Ollama model."
    );
  }

  const prompt = [
    "You are the Qwen agent inside Sona AI Console.",
    "Answer concisely and use the provided safe editor context only.",
    formatContextForPrompt(request.context),
    `User prompt:\n${request.prompt}`
  ].join("\n\n");

  const text = await callOllamaGenerate(
    qwen.url,
    qwen.model,
    prompt,
    config.timeoutMs || 30000
  );

  return {
    agentId: "qwen",
    status: "ok",
    text: text.trim() || "Qwen returned an empty response."
  };
}

function buildDeterministicLocalResponse(label: string, request: AgentRequest): string {
  const context = request.context || {};
  const lines = [
    `${label} local response.`,
    `Prompt: ${clip(request.prompt.trim() || "(empty)", MAX_PROMPT_CHARS)}`
  ];

  if (context.workspaceName) {
    lines.push(`Workspace: ${context.workspaceName}`);
  }
  if (context.currentFile) {
    lines.push(`Current file: ${context.currentFile}`);
  }
  if (context.languageId) {
    lines.push(`Language: ${context.languageId}`);
  }
  if (context.selection) {
    lines.push(`Selected text: ${clip(context.selection, MAX_SELECTION_CHARS)}`);
  }
  if (Array.isArray(context.diagnostics)) {
    lines.push(`Diagnostics included: ${context.diagnostics.length}`);
  }

  lines.push("No external provider was called.");
  return lines.join("\n");
}

function formatContextForPrompt(context: AgentContext): string {
  const safeContext = {
    currentFile: context.currentFile,
    selection: context.selection ? clip(context.selection, MAX_SELECTION_CHARS) : undefined,
    diagnostics: context.diagnostics,
    workspaceName: context.workspaceName,
    languageId: context.languageId
  };
  return `Safe editor context:\n${JSON.stringify(safeContext, null, 2)}`;
}

function callOllamaGenerate(
  baseUrl: string,
  model: string,
  prompt: string,
  timeoutMs: number
): Promise<string> {
  const url = new URL("/api/generate", normalizeOllamaUrl(baseUrl));
  const transport = url.protocol === "https:" ? https : http;
  const payload = JSON.stringify({
    model,
    prompt,
    stream: false,
    options: {
      temperature: 0.2,
      num_predict: 220
    }
  });

  return new Promise((resolve, reject) => {
    const req = transport.request(
      url,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Content-Length": Buffer.byteLength(payload)
        },
        timeout: timeoutMs
      },
      response => {
        let body = "";
        response.setEncoding("utf8");
        response.on("data", chunk => {
          body += chunk;
        });
        response.on("end", () => {
          if (!response.statusCode || response.statusCode < 200 || response.statusCode >= 300) {
            reject(new Error(`Ollama request failed with status ${response.statusCode || "unknown"}.`));
            return;
          }
          try {
            const parsed = JSON.parse(body);
            resolve(String(parsed.response || ""));
          } catch (error) {
            reject(new Error(`Failed to parse Ollama response: ${error instanceof Error ? error.message : String(error)}`));
          }
        });
      }
    );

    req.on("timeout", () => {
      req.destroy(new Error("Ollama request timed out."));
    });
    req.on("error", reject);
    req.write(payload);
    req.end();
  });
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

function clip(value: string, limit: number): string {
  if (value.length <= limit) {
    return value;
  }
  return `${value.slice(0, Math.max(0, limit - 3))}...`;
}
