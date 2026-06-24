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
var __importStar = (this && this.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (k !== "default" && Object.prototype.hasOwnProperty.call(mod, k)) __createBinding(result, mod, k);
    __setModuleDefault(result, mod);
    return result;
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.deactivate = exports.activate = void 0;
const vscode = __importStar(require("vscode"));
const sonaAiConsoleView_1 = require("./aiConsole/sonaAiConsoleView");
const sonaCliIntegration = require("../out/sonaCliIntegration");
const lspClient = require("../out/lspClient");
function shouldStartLsp(doc) {
    return Boolean(doc && doc.languageId === "sona");
}
function activate(context) {
    console.log("Sona 0.15.1 Extension is now active.");
    sonaCliIntegration.activate(context);
    const aiConsoleProvider = new sonaAiConsoleView_1.SonaAiConsoleViewProvider(context);
    context.subscriptions.push(vscode.window.registerWebviewViewProvider(sonaAiConsoleView_1.SonaAiConsoleViewProvider.viewType, aiConsoleProvider, {
        webviewOptions: {
            retainContextWhenHidden: true
        }
    }), vscode.commands.registerCommand("sona.aiConsole.focus", () => aiConsoleProvider.focus()), vscode.commands.registerCommand("sona.aiConsole.clear", () => aiConsoleProvider.clearChat()), vscode.commands.registerCommand("sona.aiConsole.selectAgent", () => aiConsoleProvider.selectAgent()));
    const maybeStart = () => {
        const active = vscode.window.activeTextEditor?.document;
        if (shouldStartLsp(active)) {
            lspClient.startSonaLsp(context);
        }
    };
    context.subscriptions.push(vscode.window.onDidChangeActiveTextEditor(() => maybeStart()));
    context.subscriptions.push(vscode.workspace.onDidOpenTextDocument(() => maybeStart()));
    maybeStart();
    const hasShownWelcome = context.globalState.get("sonaWelcomeShown");
    if (!hasShownWelcome) {
        setTimeout(() => {
            vscode.window
                .showInformationMessage("Welcome to Sona 0.15.1. Cognitive Diagnostics are ready to use.", "Get Started", "Documentation")
                .then(choice => {
                if (choice === "Get Started") {
                    vscode.commands.executeCommand("sona.welcome");
                }
                else if (choice === "Documentation") {
                    vscode.env.openExternal(vscode.Uri.parse("https://github.com/Bryantad/Sona"));
                }
            });
            context.globalState.update("sonaWelcomeShown", true);
        }, 1500);
    }
}
exports.activate = activate;
function deactivate() {
    console.log("Sona Extension deactivated");
    sonaCliIntegration.deactivate();
    void lspClient.stopSonaLsp();
}
exports.deactivate = deactivate;
//# sourceMappingURL=extension.js.map