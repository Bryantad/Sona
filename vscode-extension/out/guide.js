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
exports.guideOptions = guideOptions;
exports.guardCodeActions = guardCodeActions;
exports.activateGuide = activateGuide;
const vscode = __importStar(require("vscode"));
const crypto_1 = require("crypto");
const lspClient_1 = require("./lspClient");
const guideModel_1 = require("./guideModel");
const guideFacts_1 = require("./guideFacts");
const pythonEnvironment_1 = require("./pythonEnvironment");
let sequence = 0;
const views = new Map();
function guideOptions(uri) {
    const config = vscode.workspace.getConfiguration("sona.guide", uri);
    const options = {};
    // Omitted editor settings leave project profile defaults and scaffold decay intact.
    for (const key of ["mode", "style", "density", "quiet"]) {
        const value = config.inspect(key);
        const explicit = value?.workspaceFolderValue ?? value?.workspaceValue ?? value?.globalValue;
        if (explicit !== undefined)
            options[key] = explicit;
    }
    return options;
}
function virtualDocument(text, name) {
    const uri = vscode.Uri.parse(`sona-guide:/${++sequence}-${name}`);
    views.set(uri.toString(), text);
    while (views.size > 24)
        views.delete(views.keys().next().value);
    return uri;
}
async function showResponse(response) {
    const uri = virtualDocument((0, guideModel_1.guideText)(response), "explanation.txt");
    const document = await vscode.workspace.openTextDocument(uri);
    await vscode.window.showTextDocument(document, { viewColumn: vscode.ViewColumn.Beside, preview: true });
}
async function explainCheckedFacts(kind) {
    if (!vscode.workspace.isTrusted)
        throw new Error("Checked-fact explanations require a trusted workspace before starting Python.");
    let receipt;
    if (kind === "proof") {
        receipt = (await vscode.window.showOpenDialog({ canSelectMany: false, canSelectFiles: true,
            canSelectFolders: false, title: "Explain Proof Mode Receipt", filters: { "Proof Mode receipts": ["sproof", "json"] } }))?.[0];
        if (!receipt)
            return;
        if (receipt.scheme !== "file")
            throw new Error("Select a local receipt file.");
    }
    const resource = receipt || vscode.window.activeTextEditor?.document.uri;
    let folder = resource ? vscode.workspace.getWorkspaceFolder(resource) : undefined;
    if (!folder)
        folder = await vscode.window.showWorkspaceFolderPick({ placeHolder: "Choose the project whose runtime and preferences should be used" });
    if (!folder)
        return;
    if (folder.uri.scheme !== "file")
        throw new Error("Select a local workspace project.");
    const response = await (0, guideFacts_1.requestCheckedFacts)((0, pythonEnvironment_1.resolveSonaPythonPath)(folder.uri), kind, folder.uri.fsPath, guideOptions(folder.uri), receipt?.fsPath);
    await showResponse(response);
    if (await vscode.window.showInformationMessage("Sona Guide preserves the complete checked facts.", "Open complete JSON")) {
        await vscode.window.showTextDocument(await vscode.workspace.openTextDocument(virtualDocument(JSON.stringify(response, null, 2), "checked-facts.json")), { preview: true });
    }
}
function sourceEditor() {
    const editor = vscode.window.activeTextEditor;
    if (!editor || editor.document.languageId !== "sona")
        throw new Error("Open a Sona source document first.");
    return editor;
}
async function explainSelection(context) {
    const editor = sourceEditor();
    if (editor.selection.isEmpty)
        throw new Error("Select the Sona code you want explained.");
    const doc = editor.document;
    await showResponse(await (0, lspClient_1.requestSonaGuide)(context, (0, guideModel_1.selectionRequest)(doc.getText(), doc.uri.toString(), editor.selection, guideOptions(doc.uri))));
}
async function explainDiagnostic(context) {
    const editor = sourceEditor();
    const doc = editor.document;
    const diagnostics = vscode.languages.getDiagnostics(doc.uri).filter(item => item.source === "sona");
    if (!diagnostics.length)
        throw new Error("No Sona diagnostic is available for this document.");
    const atCursor = diagnostics.filter(item => item.range.contains(editor.selection.active));
    const candidates = atCursor.length ? atCursor : diagnostics;
    const chosen = candidates.length === 1 ? candidates[0] : (await vscode.window.showQuickPick(candidates.map(item => ({ label: item.message, description: `Line ${item.range.start.line + 1}`, item })), { title: "Sona Guide: Explain Diagnostic" }))?.item;
    if (chosen)
        await showResponse(await (0, lspClient_1.requestSonaGuide)(context, (0, guideModel_1.diagnosticRequest)(doc.getText(), doc.uri.toString(), chosen, guideOptions(doc.uri))));
}
async function showFocus(context) {
    const doc = sourceEditor().document;
    const response = await (0, lspClient_1.requestSonaGuide)(context, {
        schema_version: 1, action: "focus", source: doc.getText(), document: doc.uri.toString(), options: guideOptions(doc.uri)
    });
    // The full JSON stays available in a separate read-only document on explicit request.
    await showResponse(response);
    const choice = await vscode.window.showInformationMessage("Guide Focus preserves every canonical diagnostic.", "Open complete JSON");
    if (choice)
        await vscode.window.showTextDocument(await vscode.workspace.openTextDocument(virtualDocument(JSON.stringify(response, null, 2), "complete-diagnostics.json")), { preview: true });
}
function guardCodeActions(actions, document) {
    return actions?.map(action => {
        const command = (0, guideModel_1.previewCommand)(action, document);
        if (command) {
            action.edit = undefined;
            action.command = command;
            action.isPreferred = false;
        }
        return action;
    });
}
async function previewFix(documentUri, data) {
    const doc = vscode.workspace.textDocuments.find(item => item.uri.toString() === documentUri);
    if (!doc || doc.isClosed)
        throw new Error("The document is closed. Reopen it and request a new fix.");
    const before = doc.getText();
    const preview = (0, guideModel_1.checkedFix)(before, documentUri, doc.version, data);
    await vscode.commands.executeCommand("vscode.diff", virtualDocument(before, "before.sona"), virtualDocument(preview.text, "after.sona"), "Sona Guide: Fix Preview", { preview: true });
    const choice = await vscode.window.showInformationMessage("Review the Sona Guide edit before applying it.", "Apply fix");
    if (choice !== "Apply fix")
        return;
    const editor = await vscode.window.showTextDocument(doc);
    const current = (0, guideModel_1.checkedFix)(doc.getText(), documentUri, doc.version, data);
    // TextEditor.edit captures the document version and applies this as one undoable edit.
    const applied = await editor.edit(builder => {
        for (const edit of current.edits)
            builder.replace(new vscode.Range(doc.positionAt(edit.start), doc.positionAt(edit.end)), edit.replacement);
    });
    if (!applied)
        throw new Error("SONA-GUIDE-003: The edit could not be applied. Request a fresh preview.");
    // didChange recomputes canonical diagnostics. Editor application does not write a learning profile.
}
function sha256(text) {
    return (0, crypto_1.createHash)("sha256").update(text, "utf8").digest("hex");
}
async function proposeLocalEdit(context) {
    if (!vscode.workspace.isTrusted) {
        throw new Error("AI edit proposals require a trusted workspace before starting a local provider.");
    }
    const editor = sourceEditor();
    const document = editor.document;
    if (document.uri.scheme !== "file")
        throw new Error("AI edit proposals require a local Sona file.");
    if (editor.selection.isEmpty)
        throw new Error("Select the Sona code you want the local model to replace.");
    const original = document.getText();
    const originalVersion = document.version;
    const selectedRange = new vscode.Range(editor.selection.start, editor.selection.end);
    const selectedText = document.getText(selectedRange);
    if (Buffer.byteLength(selectedText, "utf8") > 8 * 1024) {
        throw new Error("The selected code exceeds the 8 KiB local Guide context limit.");
    }
    const folder = vscode.workspace.getWorkspaceFolder(document.uri);
    if (!folder || folder.uri.scheme !== "file")
        throw new Error("Choose a local workspace folder first.");
    const instruction = await vscode.window.showInputBox({
        title: "Sona Guide: Propose a local AI edit",
        prompt: "Describe the change. Only the selected code is sent as source context.",
        placeHolder: "For example: simplify this function without changing its behavior",
        validateInput(value) {
            if (!value.trim())
                return "Enter an edit instruction.";
            if (Buffer.byteLength(value, "utf8") > 4096)
                return "Keep the instruction under 4 KiB.";
            return undefined;
        }
    });
    if (instruction === undefined)
        return;
    const modelId = vscode.workspace.getConfiguration("sona.guide", folder.uri)
        .get("localModelId", "").trim();
    const response = await (0, lspClient_1.requestSonaLocalModelEdit)(context, {
        schema_version: 1,
        action: "local_model_proposal",
        document: document.uri.toString(),
        source: selectedText,
        instruction,
        ...(modelId ? { model_id: modelId } : {})
    });
    if (response?.schema_version !== 1
        || response.status !== "ok"
        || response.provider_id !== "local"
        || response.runtime_id !== "llama-cpp"
        || typeof response.model_id !== "string"
        || (modelId.length > 0 && response.model_id !== modelId)
        || typeof response.proposal !== "string") {
        const diagnostic = response?.diagnostic;
        const message = typeof diagnostic?.message === "string"
            ? diagnostic.message : "Direct local inference failed; no provider fallback was attempted.";
        throw new Error(message);
    }
    const replacement = (0, guideModel_1.parseEditProposal)(response.proposal);
    if (document.isClosed || document.version !== originalVersion || document.getText() !== original) {
        throw new Error("SONA-GUIDE-003: The document changed while the model was responding. Request a fresh proposal.");
    }
    const start = document.offsetAt(selectedRange.start);
    const end = document.offsetAt(selectedRange.end);
    const proposed = original.slice(0, start) + replacement + original.slice(end);
    const validation = await (0, lspClient_1.requestSonaGuide)(context, {
        schema_version: 1,
        action: "validate_proposal",
        document: document.uri.toString(),
        source: original,
        proposed_source: proposed
    });
    if (validation?.schema_version !== 1
        || validation.status !== "valid"
        || validation.validation_code !== "SONA-PROPOSAL-VALID"
        || validation.source_sha256 !== sha256(original)
        || validation.proposed_sha256 !== sha256(proposed)) {
        const code = typeof validation?.validation_code === "string"
            ? validation.validation_code : "SONA-PROPOSAL-VALIDATION-FAILED";
        throw new Error(`${code}: Sona rejected the proposed edit. No changes were applied.`);
    }
    const beforeUri = virtualDocument(original, "proposal-before.sona");
    const afterUri = virtualDocument(proposed, "proposal-after.sona");
    // Keep the source document alive while the temporary diff preview replaces the active editor.
    await vscode.window.showTextDocument(document, { preview: false, preserveFocus: true });
    await vscode.commands.executeCommand("vscode.diff", beforeUri, afterUri, "Sona Guide: Local AI Edit Proposal", { preview: true });
    const choice = await vscode.window.showInformationMessage("Sona validated this local-model proposal. Review the diff before applying it to the editor buffer.", "Apply proposal");
    if (choice !== "Apply proposal")
        return;
    if (document.isClosed) {
        throw new Error("SONA-GUIDE-003: The source document was closed during review. Reopen it and request a fresh proposal. No changes were applied.");
    }
    const activeEditor = await vscode.window.showTextDocument(document);
    const selection = {
        start: { line: selectedRange.start.line, character: selectedRange.start.character },
        end: { line: selectedRange.end.line, character: selectedRange.end.character }
    };
    const selectionMatches = () => activeEditor.selection.start.line === selection.start.line
        && activeEditor.selection.start.character === selection.start.character
        && activeEditor.selection.end.line === selection.end.line
        && activeEditor.selection.end.character === selection.end.character;
    if (document.version !== originalVersion || sha256(document.getText()) !== validation.source_sha256 || !selectionMatches()) {
        throw new Error("SONA-GUIDE-003: The document or selection changed after preview. Request a fresh proposal.");
    }
    const authorizationRequest = {
        schema_version: 1,
        document: document.uri.toString(),
        document_version: originalVersion,
        selection,
        expected_source_sha256: validation.source_sha256,
        proposed_source: proposed,
        replacement
    };
    const prepared = await (0, lspClient_1.prepareSonaGuideBufferEdit)(context, authorizationRequest);
    if (prepared?.schema_version !== 1 || prepared.status !== "prepared"
        || typeof prepared.handle !== "string"
        || prepared.effect !== "EDITOR.BUFFER_REPLACE"
        || prepared.source_sha256 !== `sha256:${validation.source_sha256}`
        || prepared.proposed_sha256 !== `sha256:${validation.proposed_sha256}`
        || prepared.replacement_sha256 !== `sha256:${sha256(replacement)}`) {
        const diagnostic = typeof prepared?.message === "string"
            ? prepared.message : "Trusted policy did not authorize this editor-buffer change.";
        const code = typeof prepared?.diagnostic_id === "string"
            ? prepared.diagnostic_id : "SONA-GUIDE-AUTH-DENIED";
        throw new Error(`${code}: ${diagnostic} No changes were applied.`);
    }
    if (document.isClosed || document.version !== originalVersion || sha256(document.getText()) !== validation.source_sha256 || !selectionMatches()) {
        throw new Error("SONA-GUIDE-003: The document or selection changed during capability preparation. Request a fresh proposal.");
    }
    const authorization = await (0, lspClient_1.consumeSonaGuideBufferEdit)(context, {
        ...authorizationRequest,
        handle: prepared.handle
    });
    if (authorization?.schema_version !== 1 || authorization.status !== "authorized"
        || authorization.effect !== "EDITOR.BUFFER_REPLACE"
        || authorization.source_sha256 !== prepared.source_sha256
        || authorization.proposed_sha256 !== prepared.proposed_sha256
        || authorization.replacement_sha256 !== prepared.replacement_sha256) {
        const diagnostic = typeof authorization?.message === "string"
            ? authorization.message : "The exact one-shot editor capability was denied.";
        const code = typeof authorization?.diagnostic_id === "string"
            ? authorization.diagnostic_id : "SONA-GUIDE-AUTH-DENIED";
        throw new Error(`${code}: ${diagnostic} No changes were applied.`);
    }
    if (document.isClosed || document.version !== originalVersion || sha256(document.getText()) !== validation.source_sha256 || !selectionMatches()) {
        throw new Error("SONA-GUIDE-003: The document or selection changed after authorization. Request a fresh proposal.");
    }
    let sourceStillCurrent = false;
    const applied = await activeEditor.edit(builder => {
        if (document.version !== originalVersion || sha256(document.getText()) !== validation.source_sha256 || !selectionMatches())
            return;
        builder.replace(selectedRange, replacement);
        sourceStillCurrent = true;
    });
    if (!applied || !sourceStillCurrent) {
        throw new Error("SONA-GUIDE-003: The document changed before approval could be applied. No edit was made.");
    }
    void vscode.window.showInformationMessage("Authorized proposal applied to the editor buffer only; save the file when ready.");
}
async function chooseMode(context) {
    const choice = await vscode.window.showQuickPick([
        { label: "Guided", description: "Explanations, examples, and next steps", value: "guided" },
        { label: "Balanced", description: "Concise explanations and next steps", value: "balanced" },
        { label: "Expert", description: "Compact diagnostics and facts", value: "expert" }
    ], { title: "Sona Guide: Choose guidance detail", placeHolder: "You can change this at any time in Sona Guide settings." });
    if (!choice)
        return;
    await vscode.workspace.getConfiguration("sona.guide").update("mode", choice.value, vscode.ConfigurationTarget.Global);
    await context.globalState.update("sonaGuideSetupShown", true);
    await (0, lspClient_1.updateGuideOptions)(guideOptions(vscode.window.activeTextEditor?.document.uri));
}
function activateGuide(context) {
    function register(name, fn) {
        context.subscriptions.push(vscode.commands.registerCommand(name, async (...args) => {
            try {
                await fn(...args);
            }
            catch (error) {
                void vscode.window.showErrorMessage(error instanceof Error ? error.message : "Sona Guide is unavailable.");
            }
        }));
    }
    context.subscriptions.push(vscode.workspace.registerTextDocumentContentProvider("sona-guide", {
        provideTextDocumentContent(uri) { return views.get(uri.toString()) || "This Guide preview expired. Request a new one."; }
    }));
    context.subscriptions.push({ dispose: () => views.clear() });
    register("sona.guide.explainDiagnostic", () => explainDiagnostic(context));
    register("sona.guide.explainSelection", () => explainSelection(context));
    register("sona.guide.focus", () => showFocus(context));
    register("sona.guide.setup", () => chooseMode(context));
    register("sona.guide.previewFix", previewFix);
    register("sona.guide.proposeEdit", () => proposeLocalEdit(context));
    register("sona.guide.explainProof", () => explainCheckedFacts("proof"));
    register("sona.guide.explainGuardian", () => explainCheckedFacts("guardian"));
    const syncOptions = () => { void (0, lspClient_1.updateGuideOptions)(guideOptions(vscode.window.activeTextEditor?.document.uri)); };
    context.subscriptions.push(vscode.workspace.onDidChangeConfiguration(event => {
        if (event.affectsConfiguration("sona.guide"))
            syncOptions();
    }));
    let prompted = false;
    const firstUse = async () => {
        if (vscode.window.activeTextEditor?.document.languageId !== "sona")
            return;
        syncOptions();
        if (prompted || context.globalState.get("sonaGuideSetupShown") || !vscode.workspace.getConfiguration("sona.guide").get("showSetup", true))
            return;
        prompted = true;
        await context.globalState.update("sonaGuideSetupShown", true);
        const choice = await vscode.window.showInformationMessage("Sona Guide can explain diagnostics and selections offline.", "Choose guidance detail");
        if (choice)
            await chooseMode(context);
    };
    context.subscriptions.push(vscode.window.onDidChangeActiveTextEditor(() => { void firstUse(); }));
    void firstUse();
}
