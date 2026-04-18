import * as vscode from 'vscode';

type Marker = {
  id: string;
  uri: string;
  start: { line: number; character: number };
  end: { line: number; character: number };
  message: string;
  createdAt: number;
  expiresAt?: number;
};

const STORAGE_KEY = 'uncertaintyMarkers.v1';

function nowMs(): number {
  return Date.now();
}

function isExpired(m: Marker, at: number): boolean {
  return typeof m.expiresAt === 'number' && m.expiresAt <= at;
}

function toRange(m: Marker): vscode.Range {
  return new vscode.Range(
    new vscode.Position(m.start.line, m.start.character),
    new vscode.Position(m.end.line, m.end.character)
  );
}

function genId(): string {
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}

function clampPositionToDoc(doc: vscode.TextDocument, pos: vscode.Position): vscode.Position {
  const line = Math.max(0, Math.min(doc.lineCount - 1, pos.line));
  const char = Math.max(0, Math.min(doc.lineAt(line).text.length, pos.character));
  return new vscode.Position(line, char);
}

function applyChangeToMarker(m: Marker, change: vscode.TextDocumentContentChangeEvent): Marker {
  const changeStart = change.range.start;
  const changeEnd = change.range.end;
  const insertedLines = change.text.split(/\r\n|\r|\n/).length - 1;
  const removedLines = changeEnd.line - changeStart.line;
  const deltaLines = insertedLines - removedLines;

  const markerStart = new vscode.Position(m.start.line, m.start.character);
  const markerEnd = new vscode.Position(m.end.line, m.end.character);

  // If change is entirely after marker, do nothing.
  if (changeStart.isAfter(markerEnd)) return m;

  // If change is entirely before marker, shift marker by delta lines.
  if (changeEnd.isBefore(markerStart)) {
    return {
      ...m,
      start: { line: m.start.line + deltaLines, character: m.start.character },
      end: { line: m.end.line + deltaLines, character: m.end.character }
    };
  }

  // Overlap: keep marker anchored to start line; expand end if lines inserted.
  return {
    ...m,
    end: { line: m.end.line + Math.max(0, deltaLines), character: m.end.character }
  };
}

export function activate(context: vscode.ExtensionContext) {
  const iconPath = vscode.Uri.joinPath(context.extensionUri, 'media', 'uncertain.svg');
  const deco = vscode.window.createTextEditorDecorationType({
    gutterIconPath: iconPath,
    gutterIconSize: 'contain',
    rangeBehavior: vscode.DecorationRangeBehavior.ClosedClosed
  });
  context.subscriptions.push(deco);

  let enabled = vscode.workspace.getConfiguration('uncertaintyMarkers').get<boolean>('enabled', true);
  let markers: Marker[] = context.workspaceState.get<Marker[]>(STORAGE_KEY, []);

  function persist() {
    return context.workspaceState.update(STORAGE_KEY, markers);
  }

  function cleanupExpired() {
    const t = nowMs();
    const before = markers.length;
    markers = markers.filter(m => !isExpired(m, t));
    if (markers.length !== before) {
      void persist();
    }
  }

  function getActiveEditor(): vscode.TextEditor | undefined {
    return vscode.window.activeTextEditor;
  }

  function getMarkersForUri(uri: vscode.Uri): Marker[] {
    const key = uri.toString();
    const t = nowMs();
    return markers.filter(m => m.uri === key && !isExpired(m, t));
  }

  function render(editor?: vscode.TextEditor) {
    if (!enabled) {
      for (const e of vscode.window.visibleTextEditors) {
        e.setDecorations(deco, []);
      }
      return;
    }

    cleanupExpired();

    const targetEditors = editor ? [editor] : vscode.window.visibleTextEditors;
    for (const e of targetEditors) {
      const list = getMarkersForUri(e.document.uri);
      const decorations: vscode.DecorationOptions[] = list.map(m => {
        return {
          range: toRange(m),
          hoverMessage: new vscode.MarkdownString(
            [`**Uncertain**`, '', m.message, '', `Created: ${new Date(m.createdAt).toLocaleString()}`].join('\n')
          )
        };
      });
      e.setDecorations(deco, decorations);
    }
  }

  context.subscriptions.push(
    vscode.workspace.onDidChangeConfiguration(e => {
      if (e.affectsConfiguration('uncertaintyMarkers.enabled')) {
        enabled = vscode.workspace.getConfiguration('uncertaintyMarkers').get<boolean>('enabled', true);
        render();
      }
    })
  );

  context.subscriptions.push(vscode.window.onDidChangeActiveTextEditor(e => render(e ?? undefined)));

  context.subscriptions.push(
    vscode.workspace.onDidChangeTextDocument(e => {
      const key = e.document.uri.toString();
      if (!markers.some(m => m.uri === key)) return;
      let updated = false;
      for (const c of e.contentChanges) {
        markers = markers.map(m => {
          if (m.uri !== key) return m;
          updated = true;
          return applyChangeToMarker(m, c);
        });
      }
      if (updated) {
        void persist();
        if (vscode.window.activeTextEditor?.document.uri.toString() === key) {
          render(vscode.window.activeTextEditor);
        }
      }
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('uncertaintyMarkers.toggleEnabled', async () => {
      const cfg = vscode.workspace.getConfiguration('uncertaintyMarkers');
      const current = cfg.get<boolean>('enabled', true);
      await cfg.update('enabled', !current, vscode.ConfigurationTarget.Global);
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('uncertaintyMarkers.mark', async () => {
      const editor = getActiveEditor();
      if (!editor) return;
      if (!enabled) return;

      const cfg = vscode.workspace.getConfiguration('uncertaintyMarkers');
      const defaultExpiryDays = cfg.get<number>('defaultExpiryDays', 0);

      const message = await vscode.window.showInputBox({
        title: 'Mark as Uncertain',
        prompt: 'What are you unsure about?',
        placeHolder: 'e.g., Unsure about edge cases / Copied from reference, not fully understood'
      });
      if (!message) return;

      const expiryPick = await vscode.window.showQuickPick(
        [
          { label: 'Never expires', days: 0 },
          { label: 'Expires in 1 day', days: 1 },
          { label: 'Expires in 7 days', days: 7 },
          { label: 'Expires in 30 days', days: 30 },
          { label: `Use default (${defaultExpiryDays || 0} days)`, days: defaultExpiryDays || 0 }
        ],
        { title: 'Expiration (optional)', placeHolder: 'Choose an expiration for this marker' }
      );
      if (!expiryPick) return;

      const sel = editor.selection;
      const start = clampPositionToDoc(editor.document, sel.start);
      const end = clampPositionToDoc(editor.document, sel.end);
      const range = sel.isEmpty ? new vscode.Range(start.line, 0, start.line, editor.document.lineAt(start.line).text.length) : new vscode.Range(start, end);

      const expiresAt = expiryPick.days > 0 ? nowMs() + expiryPick.days * 24 * 60 * 60_000 : undefined;
      const marker: Marker = {
        id: genId(),
        uri: editor.document.uri.toString(),
        start: { line: range.start.line, character: range.start.character },
        end: { line: range.end.line, character: range.end.character },
        message,
        createdAt: nowMs(),
        expiresAt
      };

      markers.push(marker);
      await persist();
      render(editor);
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('uncertaintyMarkers.clearAtCursor', async () => {
      const editor = getActiveEditor();
      if (!editor) return;
      const key = editor.document.uri.toString();
      const line = editor.selection.active.line;
      const before = markers.length;
      markers = markers.filter(m => {
        if (m.uri !== key) return true;
        return !(m.start.line <= line && line <= m.end.line);
      });
      if (markers.length !== before) {
        await persist();
        render(editor);
      }
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('uncertaintyMarkers.showAll', async () => {
      const items = markers
        .filter(m => !isExpired(m, nowMs()))
        .map(m => ({
          label: m.message,
          description: `${vscode.Uri.parse(m.uri).fsPath}`,
          detail: `Line ${m.start.line + 1} → ${m.end.line + 1}`,
          marker: m
        }));

      const picked = await vscode.window.showQuickPick(items, { title: 'Uncertainty Markers' });
      if (!picked) return;

      const uri = vscode.Uri.parse(picked.marker.uri);
      const doc = await vscode.workspace.openTextDocument(uri);
      const editor = await vscode.window.showTextDocument(doc);
      const range = toRange(picked.marker);
      editor.revealRange(range, vscode.TextEditorRevealType.InCenter);
      editor.selection = new vscode.Selection(range.start, range.end);
    })
  );

  cleanupExpired();
  render();
}

export function deactivate() {}
