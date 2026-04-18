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
function debounce(fn, ms) {
    let timer;
    return () => {
        if (timer)
            clearTimeout(timer);
        timer = setTimeout(fn, ms);
    };
}
function activate(context) {
    const status = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 98);
    status.command = 'cognitiveDrift.showActions';
    context.subscriptions.push(status);
    let enabled = vscode.workspace.getConfiguration('cognitiveDrift').get('enabled', true);
    let lastEditAt = Date.now();
    let lastShownHighAt = 0;
    const switches = [];
    function getConfig() {
        const cfg = vscode.workspace.getConfiguration('cognitiveDrift');
        return {
            enabled: cfg.get('enabled', true),
            lookbackMinutes: cfg.get('lookbackMinutes', 8),
            switchesForHigh: cfg.get('switchesForHigh', 10),
            idleSeconds: cfg.get('idleSeconds', 90),
            notifications: cfg.get('notifications', false)
        };
    }
    function prune(now) {
        const cutoff = now - getConfig().lookbackMinutes * 60_000;
        while (switches.length > 0 && switches[0].at < cutoff) {
            switches.shift();
        }
    }
    function computeLevel(now) {
        const cfg = getConfig();
        prune(now);
        const idle = now - lastEditAt >= cfg.idleSeconds * 1000;
        const switchCount = switches.length;
        // backtracking = A->B->A patterns in recent history
        let backtracks = 0;
        for (let i = 2; i < switches.length; i++) {
            if (switches[i].uri === switches[i - 2].uri && switches[i].uri !== switches[i - 1].uri) {
                backtracks++;
            }
        }
        const switchScore = Math.min(1, switchCount / cfg.switchesForHigh);
        const backtrackScore = Math.min(1, backtracks / 5);
        const idleScore = idle ? 1 : 0;
        const score = Math.min(1, 0.5 * switchScore + 0.3 * backtrackScore + 0.2 * idleScore);
        const level = score < 0.33 ? 'Low' : score < 0.66 ? 'Medium' : 'High';
        const details = `switches=${switchCount}, backtracks=${backtracks}, idle=${idle ? 'yes' : 'no'}`;
        return { level, score, details };
    }
    function updateStatus() {
        const cfg = getConfig();
        enabled = cfg.enabled;
        if (!enabled) {
            status.hide();
            return;
        }
        const now = Date.now();
        const { level, score, details } = computeLevel(now);
        const icon = level === 'Low' ? '🟢' : level === 'Medium' ? '🟡' : '🔴';
        status.text = `${icon} Drift: ${level}`;
        status.tooltip = new vscode.MarkdownString([`**Cognitive Drift Detector**`, '', `Level: **${level}**`, `Score: **${score.toFixed(2)}**`, '', details, '', 'Click for re-orient actions.'].join('\n'));
        status.show();
        if (cfg.notifications && level === 'High' && now - lastShownHighAt > 10 * 60_000) {
            lastShownHighAt = now;
            void vscode.window.showInformationMessage('Cognitive drift looks high — you may want to re-orient or add context.', 'Re-orient', 'Dismiss')
                .then(choice => {
                if (choice === 'Re-orient') {
                    void vscode.commands.executeCommand('cognitiveDrift.showActions');
                }
            });
        }
    }
    const debouncedUpdate = debounce(updateStatus, 300);
    context.subscriptions.push(vscode.workspace.onDidChangeConfiguration(e => {
        if (e.affectsConfiguration('cognitiveDrift')) {
            updateStatus();
        }
    }));
    context.subscriptions.push(vscode.window.onDidChangeActiveTextEditor(editor => {
        if (!enabled)
            return;
        if (!editor)
            return;
        if (editor.document.isUntitled)
            return;
        switches.push({ at: Date.now(), uri: editor.document.uri.toString() });
        debouncedUpdate();
    }));
    context.subscriptions.push(vscode.workspace.onDidChangeTextDocument(() => {
        lastEditAt = Date.now();
        debouncedUpdate();
    }));
    context.subscriptions.push(vscode.commands.registerCommand('cognitiveDrift.toggleEnabled', async () => {
        const cfg = vscode.workspace.getConfiguration('cognitiveDrift');
        const current = cfg.get('enabled', true);
        await cfg.update('enabled', !current, vscode.ConfigurationTarget.Global);
        updateStatus();
    }));
    context.subscriptions.push(vscode.commands.registerCommand('cognitiveDrift.reset', async () => {
        switches.splice(0, switches.length);
        lastEditAt = Date.now();
        updateStatus();
    }));
    context.subscriptions.push(vscode.commands.registerCommand('cognitiveDrift.showActions', async () => {
        const actions = [
            {
                label: 'Re-orient: Open Recent Files',
                command: 'workbench.action.quickOpenRecent'
            },
            {
                label: 'Re-orient: Show Open Editors',
                command: 'workbench.action.showAllEditors'
            },
            {
                label: 'Re-orient: Focus Explorer',
                command: 'workbench.view.explorer'
            }
        ];
        const picked = await vscode.window.showQuickPick(actions, { title: 'Cognitive Drift: Re-orient actions' });
        if (!picked)
            return;
        await vscode.commands.executeCommand(picked.command);
    }));
    updateStatus();
}
function deactivate() { }
//# sourceMappingURL=extension.js.map