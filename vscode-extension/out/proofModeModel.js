"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.parseProofModeCliOutput = parseProofModeCliOutput;
const capabilityLabels = [
    ["console", "console"],
    ["filesystem_read", "fs.read"],
    ["filesystem_write", "fs.write"],
    ["network", "network"],
    ["process", "process"],
    ["environment", "environment"]
];
function asObject(value, label) {
    if (!value || typeof value !== "object" || Array.isArray(value)) {
        throw new Error(`${label} is unavailable`);
    }
    return value;
}
function requiredString(value, label) {
    if (typeof value !== "string" || !value) {
        throw new Error(`${label} is unavailable`);
    }
    return value;
}
function requiredBoolean(value, label) {
    if (typeof value !== "boolean") {
        throw new Error(`${label} is unavailable`);
    }
    return value;
}
function requiredInteger(value, label) {
    if (!Number.isInteger(value)) {
        throw new Error(`${label} is unavailable`);
    }
    return value;
}
function identity(label, value) {
    const record = asObject(value, `${label} identity`);
    return {
        label,
        bytes: requiredInteger(record.bytes, `${label} byte count`),
        sha256: requiredString(record.sha256, `${label} hash`)
    };
}
function invalidModel(payload) {
    const diagnostic = payload.diagnostic && typeof payload.diagnostic === "object"
        ? payload.diagnostic
        : {};
    return {
        state: "invalid",
        diagnosticId: typeof diagnostic.diagnostic_id === "string"
            ? diagnostic.diagnostic_id
            : undefined,
        message: typeof diagnostic.message === "string"
            ? diagnostic.message
            : "The shared Proof Mode verifier rejected this receipt."
    };
}
function effectsModel(value) {
    if (!Array.isArray(value)) {
        throw new Error("observed effects are unavailable");
    }
    const grouped = new Map();
    for (const rawEffect of value) {
        const effect = asObject(rawEffect, "observed effect");
        const scope = requiredString(effect.scope, "effect scope");
        const operation = requiredString(effect.operation, "effect operation");
        const identifier = typeof effect.effect === "string" && effect.effect
            ? effect.effect
            : `${scope}.${operation}`.toUpperCase();
        const outcome = requiredString(effect.outcome, "effect outcome");
        const support = typeof effect.support === "string" ? effect.support : undefined;
        const key = `${identifier}\u0000${outcome}\u0000${support || ""}`;
        const existing = grouped.get(key);
        if (existing) {
            existing.count += 1;
        }
        else {
            grouped.set(key, { effect: identifier, outcome, support, count: 1 });
        }
    }
    return [...grouped.values()].sort((left, right) => left.effect.localeCompare(right.effect) || left.outcome.localeCompare(right.outcome));
}
function parseProofModeCliOutput(output) {
    let decoded;
    try {
        decoded = JSON.parse(output);
    }
    catch {
        return {
            state: "unavailable",
            message: "The Sona CLI did not return machine-readable Proof Mode output."
        };
    }
    try {
        const payload = asObject(decoded, "Proof Mode result");
        if (payload.status === "invalid") {
            return invalidModel(payload);
        }
        if (payload.status !== "valid") {
            return {
                state: "unavailable",
                message: "The Sona CLI returned an unsupported Proof Mode result."
            };
        }
        const engine = asObject(payload.engine, "engine identity");
        const execution = asObject(payload.execution, "execution result");
        const program = asObject(payload.program, "program identity");
        const capabilities = asObject(payload.capabilities, "capabilities");
        const stdout = identity("stdout", execution.stdout);
        const stderr = identity("stderr", execution.stderr);
        const source = identity("source", program.source);
        const programKind = requiredString(program.kind, "program kind");
        if (programKind !== "source" && programKind !== "sbc") {
            throw new Error("program kind is unavailable");
        }
        const executionStatus = requiredString(execution.status, "execution status");
        if (executionStatus !== "ok" && executionStatus !== "failed") {
            throw new Error("execution status is unavailable");
        }
        const capabilityModel = capabilityLabels.map(([key, label]) => ({
            key,
            label,
            granted: requiredBoolean(capabilities[key], `${label} capability`)
        }));
        const identities = [source];
        let sourceRevision;
        if (engine.runtime_identity !== undefined) {
            const runtimeIdentity = asObject(engine.runtime_identity, "Native runtime identity");
            identities.push(identity("native binary", runtimeIdentity.native_binary));
            sourceRevision = typeof runtimeIdentity.source_revision === "string"
                ? runtimeIdentity.source_revision
                : undefined;
        }
        if (programKind === "sbc") {
            identities.push(identity("container", program.container));
        }
        identities.push(stdout, stderr);
        const diagnostic = execution.diagnostic && typeof execution.diagnostic === "object"
            ? execution.diagnostic
            : undefined;
        const diagnosticId = diagnostic && (typeof diagnostic.id === "string"
            ? diagnostic.id
            : typeof diagnostic.diagnostic_id === "string"
                ? diagnostic.diagnostic_id
                : undefined);
        return {
            state: "valid",
            schemaId: requiredString(payload.schema_id, "schema identity"),
            sonaVersion: requiredString(payload.sona_version, "Sona runtime identity"),
            receiptHash: requiredString(payload.receipt_hash, "receipt identity"),
            generatedAtUtc: requiredString(payload.generated_at_utc, "receipt timestamp"),
            engineLabel: requiredString(engine.label, "engine label"),
            sourceRevision,
            pythonInvolved: requiredBoolean(engine.python_required, "Python requirement")
                || requiredBoolean(engine.python_embedded, "embedded Python status"),
            fallbackUsed: requiredBoolean(engine.fallback_used, "fallback status"),
            guardianBound: requiredBoolean(payload.guardian_bound, "Guardian binding"),
            executionStatus,
            exitCode: requiredInteger(execution.exit_code, "exit code"),
            durationMs: requiredInteger(execution.duration_ms, "execution duration"),
            programKind,
            diagnosticId,
            capabilities: capabilityModel,
            effects: effectsModel(payload.effects),
            identities: [
                ...identities,
                { label: "receipt", sha256: requiredString(payload.receipt_hash, "receipt identity") }
            ]
        };
    }
    catch (error) {
        return {
            state: "unavailable",
            message: error instanceof Error
                ? `The verified result could not be displayed: ${error.message}.`
                : "The verified result could not be displayed."
        };
    }
}
