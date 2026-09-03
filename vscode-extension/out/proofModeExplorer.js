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
exports.ProofModeExplorerProvider = exports.ProofModeTreeItem = void 0;
const path = __importStar(require("path"));
const vscode = __importStar(require("vscode"));
class ProofModeTreeItem extends vscode.TreeItem {
    children;
    constructor(label, collapsibleState = vscode.TreeItemCollapsibleState.None, children = []) {
        super(label, collapsibleState);
        this.children = children;
    }
}
exports.ProofModeTreeItem = ProofModeTreeItem;
function statusItem(label, description, ok) {
    const item = new ProofModeTreeItem(label);
    item.description = description;
    item.iconPath = new vscode.ThemeIcon(ok ? "pass-filled" : "error");
    return item;
}
function group(label, children) {
    const item = new ProofModeTreeItem(label, vscode.TreeItemCollapsibleState.Expanded, children);
    item.description = String(children.length);
    return item;
}
function shortHash(value) {
    const prefix = value.startsWith("sha256:") ? "sha256:" : "";
    const digest = prefix ? value.slice(prefix.length) : value;
    return `${prefix}${digest.slice(0, 12)}…`;
}
function validReceiptItems(model, receipt, programLabel) {
    const program = new ProofModeTreeItem(programLabel || "Program identity redacted");
    program.description = model.programKind === "sbc" ? "source-backed bytecode" : "source";
    program.iconPath = new vscode.ThemeIcon("file-code");
    const execution = statusItem("Execution", `${model.executionStatus === "ok" ? "Success" : "Failed"} · exit ${model.exitCode} · ${model.durationMs} ms`, model.executionStatus === "ok");
    if (model.diagnosticId) {
        execution.tooltip = `Runtime diagnostic: ${model.diagnosticId}`;
    }
    const receiptItem = statusItem("Receipt", "Verified", true);
    receiptItem.resourceUri = receipt;
    receiptItem.contextValue = "sonaProofReceipt";
    receiptItem.tooltip = `${path.basename(receipt.fsPath)}\n${model.receiptHash}`;
    receiptItem.command = {
        command: "sona.proofMode.openReceipt",
        title: "Open Proof Mode Receipt",
        arguments: [receipt]
    };
    const runtime = new ProofModeTreeItem("Runtime");
    runtime.description = `${model.engineLabel} · Sona ${model.sonaVersion}`;
    runtime.iconPath = new vscode.ThemeIcon("server-process");
    if (model.sourceRevision) {
        runtime.tooltip = `Build source revision: ${model.sourceRevision}`;
    }
    const python = statusItem("Python", model.pythonInvolved ? "Involved" : "Not involved", !model.pythonInvolved);
    const fallback = statusItem("Fallback", model.fallbackUsed ? "Used" : "Not used", !model.fallbackUsed);
    const guardian = new ProofModeTreeItem("Guardian");
    guardian.description = model.guardianBound ? "Bound" : "Unbound";
    guardian.iconPath = new vscode.ThemeIcon(model.guardianBound ? "shield" : "shield-x");
    const sourceRevision = model.sourceRevision
        ? new ProofModeTreeItem("Source revision")
        : undefined;
    if (sourceRevision && model.sourceRevision) {
        sourceRevision.description = model.sourceRevision;
        sourceRevision.tooltip = ("Build-supplied correlation identity; this is not authenticated provenance.");
        sourceRevision.iconPath = new vscode.ThemeIcon("git-commit");
    }
    const capabilities = model.capabilities.map(capability => {
        const item = new ProofModeTreeItem(capability.label);
        item.description = capability.granted ? "granted" : "denied";
        item.iconPath = new vscode.ThemeIcon(capability.granted ? "pass-filled" : "circle-slash");
        item.tooltip = `${capability.key}: ${capability.granted ? "granted" : "denied"}`;
        return item;
    });
    const effects = model.effects.length
        ? model.effects.map(effect => {
            const item = new ProofModeTreeItem(effect.effect);
            const count = effect.count === 1 ? "1 observation" : `${effect.count} observations`;
            item.description = `${count} · ${effect.outcome}`;
            item.tooltip = effect.support
                ? `${effect.effect}: ${effect.outcome} (${effect.support})`
                : `${effect.effect}: ${effect.outcome}`;
            item.iconPath = new vscode.ThemeIcon(effect.outcome === "allowed" ? "eye" : "warning");
            return item;
        })
        : [new ProofModeTreeItem("No effects recorded")];
    const identities = model.identities.map(identity => {
        const item = new ProofModeTreeItem(identity.label);
        item.description = identity.bytes === undefined
            ? shortHash(identity.sha256)
            : `${identity.bytes} B · ${shortHash(identity.sha256)}`;
        item.tooltip = identity.sha256;
        item.iconPath = new vscode.ThemeIcon("fingerprint");
        return item;
    });
    return [
        program,
        execution,
        receiptItem,
        runtime,
        ...(sourceRevision ? [sourceRevision] : []),
        python,
        fallback,
        guardian,
        group("Capabilities", capabilities),
        group("Observed Effects", effects),
        group("Evidence Identities", identities)
    ];
}
class ProofModeExplorerProvider {
    static viewType = "sona.proofModeExplorer";
    changed = new vscode.EventEmitter();
    state = { kind: "idle" };
    onDidChangeTreeData = this.changed.event;
    getTreeItem(element) {
        return element;
    }
    getChildren(element) {
        if (element) {
            return element.children;
        }
        if (this.state.kind === "running") {
            const item = new ProofModeTreeItem(`Running ${this.state.programLabel}`);
            item.description = "Proof Mode";
            item.iconPath = new vscode.ThemeIcon("loading~spin");
            return [item];
        }
        if (this.state.kind === "error") {
            const item = statusItem("Proof Mode command", "Failed", false);
            item.tooltip = this.state.message;
            return [item];
        }
        if (this.state.kind === "receipt") {
            const { model, receipt, programLabel } = this.state;
            if (model.state === "valid") {
                return validReceiptItems(model, receipt, programLabel);
            }
            const receiptItem = statusItem("Receipt", model.state === "invalid" ? "Invalid" : "Unavailable", false);
            receiptItem.resourceUri = receipt;
            receiptItem.contextValue = "sonaProofReceipt";
            receiptItem.command = {
                command: "sona.proofMode.openReceipt",
                title: "Open Proof Mode Receipt",
                arguments: [receipt]
            };
            const message = new ProofModeTreeItem(model.state === "invalid" && model.diagnosticId
                ? model.diagnosticId
                : "Receipt details unavailable");
            message.tooltip = model.message;
            return [receiptItem, message];
        }
        const welcome = new ProofModeTreeItem("No receipt inspected");
        welcome.description = "Run or inspect Proof Mode";
        welcome.iconPath = new vscode.ThemeIcon("shield");
        welcome.command = {
            command: "sona.proofMode.inspectReceipt",
            title: "Inspect Proof Mode Receipt"
        };
        return [welcome];
    }
    getCurrentReceipt() {
        return this.state.kind === "receipt" ? this.state.receipt : undefined;
    }
    showRunning(programLabel) {
        this.state = { kind: "running", programLabel };
        this.changed.fire(undefined);
    }
    showReceipt(receipt, model, programLabel) {
        const retainedLabel = this.state.kind === "receipt"
            && this.state.receipt.toString() === receipt.toString()
            ? this.state.programLabel
            : undefined;
        this.state = {
            kind: "receipt",
            receipt,
            model,
            programLabel: programLabel || retainedLabel
        };
        this.changed.fire(undefined);
    }
    showError(message) {
        this.state = { kind: "error", message };
        this.changed.fire(undefined);
    }
    dispose() {
        this.changed.dispose();
    }
}
exports.ProofModeExplorerProvider = ProofModeExplorerProvider;
