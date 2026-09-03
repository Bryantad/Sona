import * as path from "path";
import * as vscode from "vscode";

import { ProofModeModel, ValidProofModeModel } from "./proofModeModel";

type ExplorerState =
  | { kind: "idle" }
  | { kind: "running"; programLabel: string }
  | {
      kind: "receipt";
      receipt: vscode.Uri;
      programLabel?: string;
      model: ProofModeModel;
    }
  | { kind: "error"; message: string };

export class ProofModeTreeItem extends vscode.TreeItem {
  constructor(
    label: string,
    collapsibleState = vscode.TreeItemCollapsibleState.None,
    public readonly children: ProofModeTreeItem[] = []
  ) {
    super(label, collapsibleState);
  }
}

function statusItem(label: string, description: string, ok: boolean): ProofModeTreeItem {
  const item = new ProofModeTreeItem(label);
  item.description = description;
  item.iconPath = new vscode.ThemeIcon(ok ? "pass-filled" : "error");
  return item;
}

function group(label: string, children: ProofModeTreeItem[]): ProofModeTreeItem {
  const item = new ProofModeTreeItem(
    label,
    vscode.TreeItemCollapsibleState.Expanded,
    children
  );
  item.description = String(children.length);
  return item;
}

function shortHash(value: string): string {
  const prefix = value.startsWith("sha256:") ? "sha256:" : "";
  const digest = prefix ? value.slice(prefix.length) : value;
  return `${prefix}${digest.slice(0, 12)}…`;
}

function validReceiptItems(
  model: ValidProofModeModel,
  receipt: vscode.Uri,
  programLabel?: string
): ProofModeTreeItem[] {
  const program = new ProofModeTreeItem(programLabel || "Program identity redacted");
  program.description = model.programKind === "sbc" ? "source-backed bytecode" : "source";
  program.iconPath = new vscode.ThemeIcon("file-code");

  const execution = statusItem(
    "Execution",
    `${model.executionStatus === "ok" ? "Success" : "Failed"} · exit ${model.exitCode} · ${model.durationMs} ms`,
    model.executionStatus === "ok"
  );
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

  const python = statusItem(
    "Python",
    model.pythonInvolved ? "Involved" : "Not involved",
    !model.pythonInvolved
  );
  const fallback = statusItem(
    "Fallback",
    model.fallbackUsed ? "Used" : "Not used",
    !model.fallbackUsed
  );
  const guardian = new ProofModeTreeItem("Guardian");
  guardian.description = model.guardianBound ? "Bound" : "Unbound";
  guardian.iconPath = new vscode.ThemeIcon(model.guardianBound ? "shield" : "shield-x");

  const sourceRevision = model.sourceRevision
    ? new ProofModeTreeItem("Source revision")
    : undefined;
  if (sourceRevision && model.sourceRevision) {
    sourceRevision.description = model.sourceRevision;
    sourceRevision.tooltip = (
      "Build-supplied correlation identity; this is not authenticated provenance."
    );
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
        item.iconPath = new vscode.ThemeIcon(
          effect.outcome === "allowed" ? "eye" : "warning"
        );
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

export class ProofModeExplorerProvider implements vscode.TreeDataProvider<ProofModeTreeItem> {
  public static readonly viewType = "sona.proofModeExplorer";

  private readonly changed = new vscode.EventEmitter<ProofModeTreeItem | undefined>();
  private state: ExplorerState = { kind: "idle" };

  public readonly onDidChangeTreeData = this.changed.event;

  getTreeItem(element: ProofModeTreeItem): vscode.TreeItem {
    return element;
  }

  getChildren(element?: ProofModeTreeItem): ProofModeTreeItem[] {
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
      const receiptItem = statusItem(
        "Receipt",
        model.state === "invalid" ? "Invalid" : "Unavailable",
        false
      );
      receiptItem.resourceUri = receipt;
      receiptItem.contextValue = "sonaProofReceipt";
      receiptItem.command = {
        command: "sona.proofMode.openReceipt",
        title: "Open Proof Mode Receipt",
        arguments: [receipt]
      };
      const message = new ProofModeTreeItem(
        model.state === "invalid" && model.diagnosticId
          ? model.diagnosticId
          : "Receipt details unavailable"
      );
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

  getCurrentReceipt(): vscode.Uri | undefined {
    return this.state.kind === "receipt" ? this.state.receipt : undefined;
  }

  showRunning(programLabel: string): void {
    this.state = { kind: "running", programLabel };
    this.changed.fire(undefined);
  }

  showReceipt(receipt: vscode.Uri, model: ProofModeModel, programLabel?: string): void {
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

  showError(message: string): void {
    this.state = { kind: "error", message };
    this.changed.fire(undefined);
  }

  dispose(): void {
    this.changed.dispose();
  }
}
