"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.getProviderStatus = getProviderStatus;
exports.routeAgentRequest = routeAgentRequest;
exports.resolveQwenConfig = resolveQwenConfig;
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const agentRegistry_1 = require("./agentRegistry");
const DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434";
const DEFAULT_QWEN_MODEL = "qwen2.5-coder:7b";
function getProviderStatus(config) {
    const qwen = resolveQwenConfig(config);
    const registryConfig = {
        qwenConfigured: qwen.configured,
        claudeConfigured: false,
        codexConfigured: false
    };
    return {
        agents: (0, agentRegistry_1.getAgents)(registryConfig),
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
async function routeAgentRequest(request, config) {
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
    }
    catch (error) {
        return {
            agentId: request.agentId,
            status: "error",
            text: error instanceof Error ? error.message : String(error)
        };
    }
}
function resolveQwenConfig(config) {
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
function readWorkspaceOllamaEnv(workspaceFolderPaths) {
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
function parseDotenv(content) {
    const parsed = {};
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
function isQwenModel(model) {
    return Boolean(model && model.toLowerCase().includes("qwen"));
}
function normalizeOllamaUrl(url) {
    const trimmed = clean(url) || DEFAULT_OLLAMA_URL;
    const withProtocol = /^https?:\/\//i.test(trimmed) ? trimmed : `http://${trimmed}`;
    return withProtocol.replace(/\/+$/, "");
}
function clean(value) {
    const trimmed = (value || "").trim();
    return trimmed || undefined;
}
