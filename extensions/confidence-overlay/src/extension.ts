import * as vscode from 'vscode';

type ConfidenceLevel = 'high' | 'medium' | 'low';

type Overlay = {
  id: string;
  uri: string;
  start: { line: number; character: number };
  end: { line: number; character: number };
  level: ConfidenceLevel;
  createdAt: number;
};

const STORAGE_KEY = 'confidenceOverlay.v1';

function genId(): string {
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}

function toRange(o: Overlay): vscode.Range {
  return new vscode.Range(
    new vscode.Position(o.start.line, o.start.character),
    new vscode.Position(o.end.line, o.end.character)
  );
}

function applyChangeToOverlay(o: Overlay, change: vscode.TextDocumentContentChangeEvent): Overlay {
  const changeStart = change.range.start;
  const changeEnd = change.range.end;
  const insertedLines = change.text.split(/\r\n|\r|\n/).length - 1;
  const removedLines = changeEnd.line - changeStart.line;
  const deltaLines = insertedLines - removedLines;

  const overlayStart = new vscode.Position(o.start.line, o.start.character);
  const overlayEnd = new vscode.Position(o.end.line, o.end.character);

  if (changeStart.isAfter(overlayEnd)) return o;
  if (changeEnd.isBefore(overlayStart)) {
    return {
      ...o,
      start: { line: o.start.line + deltaLines, character: o.start.character },
      end: { line: o.end.line + deltaLines, character: o.end.character }
    };
  }

  return {
    ...o,
    end: { line: o.end.line + Math.max(0, deltaLines), character: o.end.character }
  };
}

export function activate(context: vscode.ExtensionContext) {
  const highDeco = vscode.window.createTextEditorDecorationType({
    isWholeLine: false,
    backgroundColor: 'rgba(34, 197, 94, 0.10)'
  });
  const medDeco = vscode.window.createTextEditorDecorationType({
    isWholeLine: false,
    backgroundColor: 'rgba(234, 179, 8, 0.12)'
  });
  const lowDeco = vscode.window.createTextEditorDecorationType({
    isWholeLine: false,
    backgroundColor: 'rgba(239, 68, 68, 0.12)'
  });
  context.subscriptions.push(highDeco, medDeco, lowDeco);

  let enabled = vscode.workspace.getConfiguration('confidenceOverlay').get<boolean>('enabled', true);
  let overlays: Overlay[] = context.workspaceState.get<Overlay[]>(STORAGE_KEY, []);

  function persist() {
    return context.workspaceState.update(STORAGE_KEY, overlays);
  }

  function render(editor?: vscode.TextEditor) {
    if (!enabled) {
      for (const e of vscode.window.visibleTextEditors) {
        e.setDecorations(highDeco, []);
        e.setDecorations(medDeco, []);
        e.setDecorations(lowDeco, []);
      }
      return;
    }

    const editors = editor ? [editor] : vscode.window.visibleTextEditors;
    for (const e of editors) {
      const key = e.document.uri.toString();
      const related = overlays.filter(o => o.uri === key);

      const hi: vscode.DecorationOptions[] = [];
      const med: vscode.DecorationOptions[] = [];
      const lo: vscode.DecorationOptions[] = [];

      for (const o of related) {
        const range = toRange(o);
        const hover = new vscode.MarkdownString(
          [`**Confidence: ${o.level.toUpperCase()}**`, '', `Created: ${new Date(o.createdAt).toLocaleString()}`].join('\n')
        );
        const opt = { range, hoverMessage: hover };
        if (o.level === 'high') hi.push(opt);
        else if (o.level === 'medium') med.push(opt);
        else lo.push(opt);
      }

      e.setDecorations(highDeco, hi);
      e.setDecorations(medDeco, med);
      e.setDecorations(lowDeco, lo);
    }
  }

  function addOverlay(level: ConfidenceLevel) {
    const editor = vscode.window.activeTextEditor;
    if (!editor) return;
    if (!enabled) return;
    const sel = editor.selection;
    if (sel.isEmpty) return;

    const o: Overlay = {
      id: genId(),
      uri: editor.document.uri.toString(),
      start: { line: sel.start.line, character: sel.start.character },
      end: { line: sel.end.line, character: sel.end.character },
      level,
      createdAt: Date.now()
    };
    overlays.push(o);
    void persist();
    render(editor);
  }

  context.subscriptions.push(
    vscode.workspace.onDidChangeConfiguration(e => {
      if (e.affectsConfiguration('confidenceOverlay.enabled')) {
        enabled = vscode.workspace.getConfiguration('confidenceOverlay').get<boolean>('enabled', true);
        render();
      }
    })
  );

  context.subscriptions.push(vscode.window.onDidChangeActiveTextEditor(e => render(e ?? undefined)));

  context.subscriptions.push(
    vscode.workspace.onDidChangeTextDocument(e => {
      const key = e.document.uri.toString();
      if (!overlays.some(o => o.uri === key)) return;
      for (const c of e.contentChanges) {
        overlays = overlays.map(o => (o.uri === key ? applyChangeToOverlay(o, c) : o));
      }
      void persist();
      if (vscode.window.activeTextEditor?.document.uri.toString() === key) {
        render(vscode.window.activeTextEditor);
      }
    })
  );

  context.subscriptions.push(vscode.commands.registerCommand('confidenceOverlay.setHigh', () => addOverlay('high')));
  context.subscriptions.push(vscode.commands.registerCommand('confidenceOverlay.setMedium', () => addOverlay('medium')));
  context.subscriptions.push(vscode.commands.registerCommand('confidenceOverlay.setLow', () => addOverlay('low')));

  context.subscriptions.push(
    vscode.commands.registerCommand('confidenceOverlay.clearAtCursor', async () => {
      const editor = vscode.window.activeTextEditor;
      if (!editor) return;
      const key = editor.document.uri.toString();
      const line = editor.selection.active.line;
      const before = overlays.length;
      overlays = overlays.filter(o => {
        if (o.uri !== key) return true;
        return !(o.start.line <= line && line <= o.end.line);
      });
      if (overlays.length !== before) {
        await persist();
        render(editor);
      }
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('confidenceOverlay.clearAllInFile', async () => {
      const editor = vscode.window.activeTextEditor;
      if (!editor) return;
      const key = editor.document.uri.toString();
      const before = overlays.length;
      overlays = overlays.filter(o => o.uri !== key);
      if (overlays.length !== before) {
        await persist();
        render(editor);
      }
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('confidenceOverlay.toggleEnabled', async () => {
      const cfg = vscode.workspace.getConfiguration('confidenceOverlay');
      const current = cfg.get<boolean>('enabled', true);
      await cfg.update('enabled', !current, vscode.ConfigurationTarget.Global);
    })
  );

  render();
}

export function deactivate() {}
