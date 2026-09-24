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
exports.RuntimeViewProvider = void 0;
const vscode = __importStar(require("vscode"));
class RuntimeTreeItem extends vscode.TreeItem {
    children;
    constructor(label, collapsibleState = vscode.TreeItemCollapsibleState.None, children = [], description, icon) {
        super(label, collapsibleState);
        this.children = children;
        this.description = description;
        if (icon) {
            this.iconPath = new vscode.ThemeIcon(icon);
        }
    }
}
function isRecord(value) {
    return typeof value === "object" && value !== null && !Array.isArray(value);
}
function isCount(value) {
    return typeof value === "number" && Number.isSafeInteger(value) && value >= 0;
}
function isString(value) {
    return typeof value === "string";
}
function parseRuntimeSnapshot(output) {
    const parsed = JSON.parse(output);
    if (!isRecord(parsed) ||
        parsed.schema_version !== 1 ||
        parsed.status !== "ok" ||
        !isRecord(parsed.models) ||
        !isCount(parsed.models.registered) ||
        !Array.isArray(parsed.models.items) ||
        !parsed.models.items.every(item => isRecord(item) &&
            isString(item.model_id) &&
            isString(item.provider_id) &&
            typeof item.enabled === "boolean") ||
        !isRecord(parsed.workflows) ||
        !isCount(parsed.workflows.persisted) ||
        !isCount(parsed.workflows.active) ||
        !Array.isArray(parsed.workflows.items) ||
        !parsed.workflows.items.every(item => isRecord(item) &&
            isString(item.workflow_id) &&
            isString(item.state) &&
            isRecord(item.progress) &&
            isCount(item.progress.completed_steps) &&
            isCount(item.progress.total_steps) &&
            typeof item.progress.percent_complete === "number" &&
            Number.isFinite(item.progress.percent_complete)) ||
        !isRecord(parsed.services) ||
        !isString(parsed.services.status) ||
        !isString(parsed.services.detail) ||
        !isRecord(parsed.guardian) ||
        !isString(parsed.guardian.scope) ||
        !isString(parsed.guardian.inspect_with) ||
        !isRecord(parsed.proof) ||
        !isString(parsed.proof.receipt_schema) ||
        !isString(parsed.proof.scope) ||
        !isRecord(parsed.resource_limits)
        || !isString(parsed.resource_limits.status)
        || !(parsed.resource_limits.configured_budgets === null || isCount(parsed.resource_limits.configured_budgets))
        || !Array.isArray(parsed.resource_limits.classification)
        || !parsed.resource_limits.classification.every(isString)
        || !isString(parsed.resource_limits.measurement)) {
        throw new Error("Runtime status response does not match schema 1.");
    }
    return parsed;
}
function group(label, children, description) {
    return new RuntimeTreeItem(label, vscode.TreeItemCollapsibleState.Expanded, children, description, "server-process");
}
class RuntimeViewProvider {
    loadStatus;
    static viewType = "sona.runtimeView";
    changed = new vscode.EventEmitter();
    snapshot;
    loading = false;
    unavailable = false;
    onDidChangeTreeData = this.changed.event;
    constructor(loadStatus) {
        this.loadStatus = loadStatus;
    }
    getTreeItem(element) {
        return element;
    }
    getChildren(element) {
        if (element) {
            return element.children;
        }
        if (this.loading) {
            return [new RuntimeTreeItem("Refreshing runtime status…", undefined, [], undefined, "loading~spin")];
        }
        if (this.unavailable || !this.snapshot) {
            const item = new RuntimeTreeItem("Runtime status unavailable", undefined, [], "Run `sona runtime status --format json` to diagnose", "warning");
            return [item];
        }
        return this.createItems(this.snapshot);
    }
    async refresh() {
        if (this.loading) {
            return;
        }
        this.loading = true;
        this.changed.fire(undefined);
        try {
            const result = await this.loadStatus();
            if (!result.success) {
                throw new Error("Runtime status command failed.");
            }
            this.snapshot = parseRuntimeSnapshot(result.output);
            this.unavailable = false;
        }
        catch {
            this.snapshot = undefined;
            this.unavailable = true;
        }
        finally {
            this.loading = false;
            this.changed.fire(undefined);
        }
    }
    dispose() {
        this.changed.dispose();
    }
    createItems(snapshot) {
        const models = [
            new RuntimeTreeItem(`${snapshot.models.registered} registered · load state not probed`, undefined, [], undefined, "database"),
            ...snapshot.models.items.map(model => new RuntimeTreeItem(model.model_id, undefined, [], `${model.provider_id} · ${model.enabled ? "enabled" : "disabled"}`, "symbol-class"))
        ];
        const workflows = [
            new RuntimeTreeItem(`${snapshot.workflows.persisted} persisted · ${snapshot.workflows.active} active`, undefined, [], "Journal reads do not resume or execute work", "history"),
            ...snapshot.workflows.items.map(workflow => new RuntimeTreeItem(workflow.workflow_id, undefined, [], `${workflow.state} · ${Math.round(workflow.progress.percent_complete)}%`, workflow.state === "failed" ? "error" : "history"))
        ];
        return [
            group("Local AI", models, String(snapshot.models.registered)),
            group("Workflows", workflows, String(snapshot.workflows.active)),
            group("Services", [new RuntimeTreeItem(snapshot.services.detail, undefined, [], undefined, "info")], "Process-local"),
            group("Guardian", [new RuntimeTreeItem(snapshot.guardian.inspect_with, undefined, [], undefined, "shield")], "Project-scoped"),
            group("Proof Mode", [new RuntimeTreeItem(snapshot.proof.scope, undefined, [], undefined, "verified")], snapshot.proof.receipt_schema),
            group("Resource budgets", [new RuntimeTreeItem(`${snapshot.resource_limits.status} · ${snapshot.resource_limits.measurement}`, undefined, [], snapshot.resource_limits.classification.join(" · "), "dashboard")])
        ];
    }
}
exports.RuntimeViewProvider = RuntimeViewProvider;
