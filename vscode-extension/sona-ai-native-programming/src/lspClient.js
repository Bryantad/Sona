"use strict";
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.stopSonaLsp = exports.startSonaLsp = void 0;
const vscode = require("vscode");
const node_1 = require("vscode-languageclient/node");
let client;
function startSonaLsp(context) {
    if (client)
        return;
    const cfg = vscode.workspace.getConfiguration('sona');
    const pythonPath = cfg.get('pythonPath') || cfg.get('cli.pythonPath') || 'python';
    const serverOptions = {
        command: pythonPath,
        args: ['-m', 'sona.lsp_server', '--stdio']
    };
    const clientOptions = {
        documentSelector: [{ scheme: 'file', language: 'sona' }],
        outputChannel: vscode.window.createOutputChannel('Sona LSP')
    };
    client = new node_1.LanguageClient('sona-lsp', 'Sona Language Server', serverOptions, clientOptions);
    context.subscriptions.push(client.start());
}
exports.startSonaLsp = startSonaLsp;
function stopSonaLsp() {
    return __awaiter(this, void 0, void 0, function* () {
        if (!client)
            return;
        const toStop = client;
        client = undefined;
        yield toStop.stop();
    });
}
exports.stopSonaLsp = stopSonaLsp;
//# sourceMappingURL=lspClient.js.map