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
exports.getNearbyCommit = getNearbyCommit;
const path = __importStar(require("path"));
const vscode = __importStar(require("vscode"));
const child_process_1 = require("child_process");
function getNearbyCommit(filePath, line) {
    const config = vscode.workspace.getConfiguration('codeContext');
    if (!config.get('showGitBlameHint', true)) {
        return undefined;
    }
    try {
        const dir = path.dirname(filePath);
        const result = (0, child_process_1.execSync)(`git blame -L ${line + 1},${line + 1} --porcelain "${path.basename(filePath)}"`, { cwd: dir, encoding: 'utf8', timeout: 2000 });
        const match = result.match(/^([a-f0-9]{40})/);
        if (match && match[1] && !match[1].startsWith('00000000')) {
            return match[1].substring(0, 7);
        }
    }
    catch {
        // Git not available or not a git repo.
    }
    return undefined;
}
//# sourceMappingURL=git.js.map