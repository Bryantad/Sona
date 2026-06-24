"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.getAgent = exports.getAgents = exports.normalizeAgentId = exports.isSonaAgentId = exports.ALL_AGENT_IDS = void 0;
const AGENT_DEFINITIONS = [
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
exports.ALL_AGENT_IDS = AGENT_DEFINITIONS.map(agent => agent.id);
function isSonaAgentId(value) {
    return typeof value === "string" && exports.ALL_AGENT_IDS.includes(value);
}
exports.isSonaAgentId = isSonaAgentId;
function normalizeAgentId(value, fallback = "sona") {
    return isSonaAgentId(value) ? value : fallback;
}
exports.normalizeAgentId = normalizeAgentId;
function getAgents(config = {}) {
    return AGENT_DEFINITIONS.map(agent => ({
        ...agent,
        configured: isAgentConfigured(agent.id, config)
    }));
}
exports.getAgents = getAgents;
function getAgent(id, config = {}) {
    const agent = getAgents(config).find(candidate => candidate.id === id);
    if (!agent) {
        throw new Error(`Unknown Sona agent: ${id}`);
    }
    return agent;
}
exports.getAgent = getAgent;
function isAgentConfigured(id, config) {
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
//# sourceMappingURL=agentRegistry.js.map