/** Transport/range handling only. All Sona knowledge and fix rules live in Python. */
export type GuideOptions = {
  mode?: "guided" | "balanced" | "expert";
  style?: "simple" | "visual" | "technical";
  density?: "focused" | "normal" | "complete";
  quiet?: boolean;
};

type Position = { line: number; character: number };
type Range = { start: Position; end: Position };

function canonicalPosition(source: string, position: Position) {
  const line = source.split(/\r?\n/)[position.line];
  if (line === undefined || position.character < 0 || position.character > line.length) {
    throw new Error("Refresh the selection against the current document.");
  }
  return { line: position.line + 1, column: Array.from(line.slice(0, position.character)).length + 1 };
}

export function selectionRequest(source: string, document: string, range: Range, options: GuideOptions) {
  const start = canonicalPosition(source, range.start);
  const end = canonicalPosition(source, range.end);
  return {
    schema_version: 1, action: "selection", source, document, options,
    selection: { start_line: start.line, start_column: start.column, end_line: end.line, end_column: end.column }
  };
}

export function diagnosticRequest(source: string, document: string, item: any, options: GuideOptions) {
  const start = canonicalPosition(source, item.range.start);
  const end = canonicalPosition(source, item.range.end);
  const identifier = typeof item.code === "object" ? item.code.value : item.code;
  const diagnostic = item.data?.diagnostic_id ? item.data : {
    diagnostic_id: identifier, category: "lsp", message: item.message,
    severity: ["error", "warning", "info", "hint"][item.severity], source: "sona-lsp",
    file: document, start_line: start.line, start_column: start.column,
    end_line: end.line, end_column: end.column
  };
  return { schema_version: 1, action: "diagnostic", source, document, diagnostic, options };
}

export function guideText(response: any): string {
  if (response?.schema_version !== 1) {
    throw new Error("The selected Sona runtime does not support the Guide JSON contract. Update it and reload VS Code.");
  }
  if (response.status === "unavailable") {
    return `${response.diagnostic?.diagnostic_id || "SONA-GUIDE-002"}: ${response.diagnostic?.message || "Guide unavailable."}\n\n${response.diagnostic?.hint || ""}`;
  }
  if (typeof response.text !== "string" || response.text.length > 1024 * 1024) {
    throw new Error("The Sona Guide response is invalid or too large.");
  }
  return response.text;
}

function sourceOffset(source: string, lineNumber: number, column: number): number {
  if (!Number.isInteger(lineNumber) || !Number.isInteger(column) || lineNumber < 1 || column < 1) {
    throw new Error("Invalid Guide edit range.");
  }
  const lines = source.split("\n");
  if (lineNumber > lines.length) throw new Error("Guide edit is outside the document.");
  const line = lines[lineNumber - 1].replace(/\r$/, "");
  const characters = Array.from(line);
  if (column > characters.length + 1) throw new Error("Guide edit is outside the line.");
  return lines.slice(0, lineNumber - 1).reduce((total, value) => total + value.length + 1, 0)
    + characters.slice(0, column - 1).join("").length;
}

export function checkedFix(source: string, document: string, version: number, data: any) {
  if (data?.schema_version !== 1 || data.source !== "sona-guide" || data.document_version !== version) {
    throw new Error("SONA-GUIDE-003: The document changed. Request a fresh fix preview.");
  }
  const fixes = data.fix?.edits;
  if (!Array.isArray(fixes) || fixes.length === 0 || fixes.length > 1000) {
    throw new Error("Invalid Guide fix preview.");
  }
  const edits = fixes.map(edit => {
    if (edit.document !== document || typeof edit.expected !== "string" || typeof edit.replacement !== "string") {
      throw new Error("Invalid Guide fix document or text.");
    }
    const start = sourceOffset(source, edit.range.start_line, edit.range.start_column);
    const end = sourceOffset(source, edit.range.end_line, edit.range.end_column);
    if (end < start || source.slice(start, end) !== edit.expected) {
      throw new Error("SONA-GUIDE-003: The expected text changed. Request a fresh fix preview.");
    }
    return { start, end, replacement: edit.replacement };
  }).sort((a, b) => a.start - b.start);
  let previousEnd = -1;
  for (const edit of edits) {
    if (edit.start < previousEnd) throw new Error("Guide fixes overlap. Refresh the preview.");
    previousEnd = edit.end;
  }
  let text = source;
  for (const edit of [...edits].reverse()) {
    text = text.slice(0, edit.start) + edit.replacement + text.slice(edit.end);
  }
  return { text, edits };
}

export function previewCommand(action: any, document: string) {
  if (action.data?.source !== "sona-guide" || action.disabled) return undefined;
  return {
    title: "Preview Sona Guide fix", command: "sona.guide.previewFix",
    arguments: [document, action.data]
  };
}
