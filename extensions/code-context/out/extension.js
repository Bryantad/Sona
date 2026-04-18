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
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = __importStar(require("vscode"));
const commands_1 = require("./commands");
const decorations_1 = require("./decorations");
const hover_1 = require("./hover");
const storage_1 = require("./storage");
const tree_1 = require("./tree");
async function activate(context) {
    const storage = new storage_1.ContextNotesStorage(context);
    await storage.load();
    const treeProvider = new tree_1.ContextNotesTreeProvider(storage);
    const statusBarItem = (0, decorations_1.createStatusBar)();
    context.subscriptions.push(statusBarItem);
    context.subscriptions.push(vscode.window.registerTreeDataProvider('codeContextNotes', treeProvider));
    context.subscriptions.push(vscode.languages.registerHoverProvider({ scheme: 'file' }, new hover_1.ContextHoverProvider(storage)));
    (0, commands_1.registerCommands)(context, storage, treeProvider, statusBarItem);
    context.subscriptions.push(vscode.window.onDidChangeActiveTextEditor((editor) => {
        if (editor) {
            (0, decorations_1.updateDecorations)(editor, storage);
            (0, decorations_1.updateStatusBar)(storage, statusBarItem);
        }
        else {
            statusBarItem.hide();
        }
    }));
    context.subscriptions.push(vscode.workspace.onDidChangeTextDocument((event) => {
        const editor = vscode.window.activeTextEditor;
        if (editor && event.document === editor.document) {
            setTimeout(() => {
                (0, decorations_1.updateDecorations)(editor, storage);
                (0, decorations_1.updateStatusBar)(storage, statusBarItem);
            }, 300);
        }
    }));
    context.subscriptions.push(vscode.workspace.onDidChangeConfiguration((event) => {
        if (event.affectsConfiguration('codeContext')) {
            const editor = vscode.window.activeTextEditor;
            if (editor) {
                (0, decorations_1.updateDecorations)(editor, storage);
                (0, decorations_1.updateStatusBar)(storage, statusBarItem);
            }
            treeProvider.refresh();
        }
    }));
    if (vscode.window.activeTextEditor) {
        (0, decorations_1.updateDecorations)(vscode.window.activeTextEditor, storage);
        (0, decorations_1.updateStatusBar)(storage, statusBarItem);
    }
    console.log('Code Context extension activated');
}
function deactivate() { }
//# sourceMappingURL=extension.js.map