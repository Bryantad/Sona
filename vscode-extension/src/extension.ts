import * as vscode from "vscode";

import { SonaAiConsoleViewProvider } from "./aiConsole/sonaAiConsoleView";

const sonaCliIntegration = require("../out/sonaCliIntegration");
const lspClient = require("../out/lspClient");

function shouldStartLsp(doc: vscode.TextDocument | undefined): boolean {
  return Boolean(doc && doc.languageId === "sona");
}

export function activate(context: vscode.ExtensionContext): void {
  console.log("Sona 0.15.1 Extension is now active.");

  sonaCliIntegration.activate(context);

  const aiConsoleProvider = new SonaAiConsoleViewProvider(context);
  context.subscriptions.push(
    vscode.window.registerWebviewViewProvider(
      SonaAiConsoleViewProvider.viewType,
      aiConsoleProvider,
      {
        webviewOptions: {
          retainContextWhenHidden: true
        }
      }
    ),
    vscode.commands.registerCommand("sona.aiConsole.focus", () => aiConsoleProvider.focus()),
    vscode.commands.registerCommand("sona.aiConsole.clear", () => aiConsoleProvider.clearChat()),
    vscode.commands.registerCommand("sona.aiConsole.selectAgent", () => aiConsoleProvider.selectAgent())
  );

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
        .showInformationMessage(
          "Welcome to Sona 0.15.1. Cognitive Diagnostics are ready to use.",
          "Get Started",
          "Documentation"
        )
        .then(choice => {
          if (choice === "Get Started") {
            vscode.commands.executeCommand("sona.welcome");
          } else if (choice === "Documentation") {
            vscode.env.openExternal(vscode.Uri.parse("https://github.com/Bryantad/Sona"));
          }
        });
      context.globalState.update("sonaWelcomeShown", true);
    }, 1500);
  }
}

export function deactivate(): void {
  console.log("Sona Extension deactivated");
  sonaCliIntegration.deactivate();
  void lspClient.stopSonaLsp();
}
