import * as vscode from "vscode";

export interface RuntimeCommandResult {
  success: boolean;
  output: string;
}

interface RuntimeModel {
  model_id: string;
  provider_id: string;
  enabled: boolean;
}

interface RuntimeLocalModel {
  model_id: string;
  runtime_id: string;
  format: string;
  context_tokens: number;
  device: string;
  is_default: boolean;
  artifact_exists: boolean;
  artifact_size_bytes: number | null;
  hash_recorded: boolean;
}

interface RuntimeWorkflow {
  workflow_id: string;
  state: string;
  progress: {
    completed_steps: number;
    total_steps: number;
    percent_complete: number;
  };
}

interface RuntimeSnapshot {
  schema_version: number;
  status: string;
  models: { registered: number; items: RuntimeModel[] };
  local_models?: {
    registered: number;
    default_model_id: string | null;
    items: RuntimeLocalModel[];
    load_state: string;
  };
  workflows: { persisted: number; active: number; items: RuntimeWorkflow[] };
  services: { status: string; detail: string };
  guardian: { scope: string; inspect_with: string };
  proof: { receipt_schema: string; scope: string };
  resource_limits: {
    status: string;
    configured_budgets: number | null;
    classification: string[];
    measurement: string;
  };
}

class RuntimeTreeItem extends vscode.TreeItem {
  constructor(
    label: string,
    collapsibleState = vscode.TreeItemCollapsibleState.None,
    public readonly children: RuntimeTreeItem[] = [],
    description?: string,
    icon?: string
  ) {
    super(label, collapsibleState);
    this.description = description;
    if (icon) {
      this.iconPath = new vscode.ThemeIcon(icon);
    }
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isCount(value: unknown): value is number {
  return typeof value === "number" && Number.isSafeInteger(value) && value >= 0;
}

function isString(value: unknown): value is string {
  return typeof value === "string";
}

function parseRuntimeSnapshot(output: string): RuntimeSnapshot {
  const parsed: unknown = JSON.parse(output);
  const localModelsValid = !isRecord(parsed) || parsed.local_models === undefined || (
    isRecord(parsed.local_models) &&
    isCount(parsed.local_models.registered) &&
    (parsed.local_models.default_model_id === null || isString(parsed.local_models.default_model_id)) &&
    isString(parsed.local_models.load_state) &&
    Array.isArray(parsed.local_models.items) &&
    parsed.local_models.items.every(item =>
      isRecord(item) &&
      isString(item.model_id) &&
      isString(item.runtime_id) &&
      isString(item.format) &&
      isCount(item.context_tokens) &&
      isString(item.device) &&
      typeof item.is_default === "boolean" &&
      typeof item.artifact_exists === "boolean" &&
      (item.artifact_size_bytes === null || isCount(item.artifact_size_bytes)) &&
      typeof item.hash_recorded === "boolean"
    )
  );
  if (
    !isRecord(parsed) ||
    parsed.schema_version !== 1 ||
    parsed.status !== "ok" ||
    !isRecord(parsed.models) ||
    !isCount(parsed.models.registered) ||
    !Array.isArray(parsed.models.items) ||
    !parsed.models.items.every(item =>
      isRecord(item) &&
      isString(item.model_id) &&
      isString(item.provider_id) &&
      typeof item.enabled === "boolean"
    ) ||
    !isRecord(parsed.workflows) ||
    !isCount(parsed.workflows.persisted) ||
    !isCount(parsed.workflows.active) ||
    !Array.isArray(parsed.workflows.items) ||
    !parsed.workflows.items.every(item =>
      isRecord(item) &&
      isString(item.workflow_id) &&
      isString(item.state) &&
      isRecord(item.progress) &&
      isCount(item.progress.completed_steps) &&
      isCount(item.progress.total_steps) &&
      typeof item.progress.percent_complete === "number" &&
      Number.isFinite(item.progress.percent_complete)
    ) ||
    !isRecord(parsed.services) ||
    !isString(parsed.services.status) ||
    !isString(parsed.services.detail) ||
    !isRecord(parsed.guardian) ||
    !isString(parsed.guardian.scope) ||
    !isString(parsed.guardian.inspect_with) ||
    !isRecord(parsed.proof) ||
    !isString(parsed.proof.receipt_schema) ||
    !isString(parsed.proof.scope) ||
    !localModelsValid
    || !isRecord(parsed.resource_limits)
    || !isString(parsed.resource_limits.status)
    || !(parsed.resource_limits.configured_budgets === null || isCount(parsed.resource_limits.configured_budgets))
    || !Array.isArray(parsed.resource_limits.classification)
    || !parsed.resource_limits.classification.every(isString)
    || !isString(parsed.resource_limits.measurement)
  ) {
    throw new Error("Runtime status response does not match schema 1.");
  }
  return parsed as unknown as RuntimeSnapshot;
}

function group(label: string, children: RuntimeTreeItem[], description?: string): RuntimeTreeItem {
  return new RuntimeTreeItem(
    label,
    vscode.TreeItemCollapsibleState.Expanded,
    children,
    description,
    "server-process"
  );
}

export class RuntimeViewProvider implements vscode.TreeDataProvider<RuntimeTreeItem> {
  public static readonly viewType = "sona.runtimeView";

  private readonly changed = new vscode.EventEmitter<RuntimeTreeItem | undefined>();
  private snapshot: RuntimeSnapshot | undefined;
  private loading = false;
  private unavailable = false;

  public readonly onDidChangeTreeData = this.changed.event;

  constructor(private readonly loadStatus: () => Promise<RuntimeCommandResult>) {}

  getTreeItem(element: RuntimeTreeItem): vscode.TreeItem {
    return element;
  }

  getChildren(element?: RuntimeTreeItem): RuntimeTreeItem[] {
    if (element) {
      return element.children;
    }
    if (this.loading) {
      return [new RuntimeTreeItem("Refreshing runtime status…", undefined, [], undefined, "loading~spin")];
    }
    if (this.unavailable || !this.snapshot) {
      const item = new RuntimeTreeItem(
        "Runtime status unavailable",
        undefined,
        [],
        "Run `sona runtime status --format json` to diagnose",
        "warning"
      );
      return [item];
    }
    return this.createItems(this.snapshot);
  }

  async refresh(): Promise<void> {
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
    } catch {
      this.snapshot = undefined;
      this.unavailable = true;
    } finally {
      this.loading = false;
      this.changed.fire(undefined);
    }
  }

  dispose(): void {
    this.changed.dispose();
  }

  private createItems(snapshot: RuntimeSnapshot): RuntimeTreeItem[] {
    const localModels = snapshot.local_models?.items || [];
    const models = [
      new RuntimeTreeItem(
        `${localModels.length} direct GGUF · ${snapshot.models.registered} provider descriptors`,
        undefined,
        [],
        snapshot.local_models?.load_state || "Direct model registry not reported by this Sona runtime",
        "database"
      ),
      ...localModels.map(model => new RuntimeTreeItem(
        model.model_id,
        undefined,
        [],
        `${model.runtime_id} · ${model.format} · ${model.context_tokens} context · ${model.device}`
          + `${model.is_default ? " · default" : ""}`
          + `${model.artifact_exists ? " · artifact present" : " · artifact missing"}`
          + `${model.hash_recorded ? " · SHA-256 recorded" : " · no SHA-256"}`,
        model.artifact_exists ? "symbol-class" : "warning"
      )),
      ...snapshot.models.items.map(
        model => new RuntimeTreeItem(
          model.model_id,
          undefined,
          [],
          `${model.provider_id} · ${model.enabled ? "enabled" : "disabled"}`,
          "symbol-class"
        )
      )
    ];

    const workflows = [
      new RuntimeTreeItem(
        `${snapshot.workflows.persisted} persisted · ${snapshot.workflows.active} active`,
        undefined,
        [],
        "Journal reads do not resume or execute work",
        "history"
      ),
      ...snapshot.workflows.items.map(
        workflow => new RuntimeTreeItem(
          workflow.workflow_id,
          undefined,
          [],
          `${workflow.state} · ${Math.round(workflow.progress.percent_complete)}%`,
          workflow.state === "failed" ? "error" : "history"
        )
      )
    ];

    return [
      group(
        "Local AI",
        models,
        `${localModels.length} direct GGUF · ${snapshot.models.registered} provider descriptors`
      ),
      group("Workflows", workflows, String(snapshot.workflows.active)),
      group(
        "Services",
        [new RuntimeTreeItem(snapshot.services.detail, undefined, [], undefined, "info")],
        "Process-local"
      ),
      group(
        "Guardian",
        [new RuntimeTreeItem(snapshot.guardian.inspect_with, undefined, [], undefined, "shield")],
        "Project-scoped"
      ),
      group(
        "Proof Mode",
        [new RuntimeTreeItem(snapshot.proof.scope, undefined, [], undefined, "verified")],
        snapshot.proof.receipt_schema
      ),
      group(
        "Resource budgets",
        [new RuntimeTreeItem(
          `${snapshot.resource_limits.status} · ${snapshot.resource_limits.measurement}`,
          undefined,
          [],
          snapshot.resource_limits.classification.join(" · "),
          "dashboard"
        )]
      )
    ];
  }
}
