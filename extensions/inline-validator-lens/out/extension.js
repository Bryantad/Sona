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
// ============================================================================
// VALIDATORS
// ============================================================================
const PATTERNS = {
    email: /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/,
    url: /^(https?:\/\/)?([\da-z.-]+)\.([a-z.]{2,6})([/\w .-]*)*\/?$/,
    uuid: /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i,
    ipv4: /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/,
    ipv6: /^(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$|^::(?:[0-9a-fA-F]{1,4}:){0,6}[0-9a-fA-F]{1,4}$|^(?:[0-9a-fA-F]{1,4}:){1,7}:$|^(?:[0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}$/,
    date: /^\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12][0-9]|3[01])(?:T(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9](?:\.\d+)?(?:Z|[+-](?:[01][0-9]|2[0-3]):[0-5][0-9])?)?$/,
    phone: /^[+]?[(]?[0-9]{1,4}[)]?[-\s./0-9]{6,}$/,
    creditCard: /^(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})$/,
    hexColor: /^#(?:[0-9a-fA-F]{3}){1,2}$/,
    json: /^\s*[{\[]/
};
const TYPE_LABELS = {
    email: 'Email',
    url: 'URL',
    uuid: 'UUID',
    ipv4: 'IPv4',
    ipv6: 'IPv6',
    date: 'Date',
    phone: 'Phone',
    creditCard: 'Card',
    hexColor: 'Color',
    json: 'JSON'
};
function detectType(value) {
    // Order matters - more specific patterns first
    if (PATTERNS.uuid.test(value))
        return 'uuid';
    if (PATTERNS.hexColor.test(value))
        return 'hexColor';
    if (PATTERNS.ipv4.test(value))
        return 'ipv4';
    if (PATTERNS.ipv6.test(value))
        return 'ipv6';
    if (PATTERNS.email.test(value))
        return 'email';
    if (PATTERNS.date.test(value))
        return 'date';
    if (PATTERNS.url.test(value))
        return 'url';
    if (PATTERNS.phone.test(value))
        return 'phone';
    if (PATTERNS.creditCard.test(value.replace(/[\s-]/g, '')))
        return 'creditCard';
    if (PATTERNS.json.test(value))
        return 'json';
    return null;
}
function validateEmail(value) {
    return PATTERNS.email.test(value);
}
function validateUrl(value) {
    try {
        new URL(value.startsWith('http') ? value : `https://${value}`);
        return true;
    }
    catch {
        return false;
    }
}
function validateUuid(value) {
    return PATTERNS.uuid.test(value);
}
function validateIpv4(value) {
    if (!PATTERNS.ipv4.test(value))
        return false;
    const parts = value.split('.').map(Number);
    return parts.every(p => p >= 0 && p <= 255);
}
function validateIpv6(value) {
    return PATTERNS.ipv6.test(value);
}
function validateDate(value) {
    if (!PATTERNS.date.test(value))
        return false;
    const date = new Date(value);
    return !isNaN(date.getTime());
}
function validatePhone(value) {
    const digits = value.replace(/\D/g, '');
    return digits.length >= 7 && digits.length <= 15;
}
function validateCreditCard(value) {
    const digits = value.replace(/[\s-]/g, '');
    if (!/^\d{13,19}$/.test(digits))
        return false;
    // Luhn algorithm
    let sum = 0;
    let isEven = false;
    for (let i = digits.length - 1; i >= 0; i--) {
        let digit = parseInt(digits[i], 10);
        if (isEven) {
            digit *= 2;
            if (digit > 9)
                digit -= 9;
        }
        sum += digit;
        isEven = !isEven;
    }
    return sum % 10 === 0;
}
function validateHexColor(value) {
    return PATTERNS.hexColor.test(value);
}
function validateJson(value) {
    try {
        JSON.parse(value);
        return true;
    }
    catch {
        return false;
    }
}
function validate(type, value) {
    switch (type) {
        case 'email': return validateEmail(value);
        case 'url': return validateUrl(value);
        case 'uuid': return validateUuid(value);
        case 'ipv4': return validateIpv4(value);
        case 'ipv6': return validateIpv6(value);
        case 'date': return validateDate(value);
        case 'phone': return validatePhone(value);
        case 'creditCard': return validateCreditCard(value);
        case 'hexColor': return validateHexColor(value);
        case 'json': return validateJson(value);
    }
}
function isTypeEnabled(config, type) {
    switch (type) {
        case 'email': return config.get('validateEmails', true);
        case 'url': return config.get('validateUrls', true);
        case 'uuid': return config.get('validateUuids', true);
        case 'ipv4':
        case 'ipv6': return config.get('validateIpAddresses', true);
        case 'date': return config.get('validateDates', true);
        case 'phone': return config.get('validatePhoneNumbers', true);
        case 'creditCard': return config.get('validateCreditCards', false);
        case 'hexColor': return config.get('validateHexColors', true);
        case 'json': return config.get('validateJson', true);
    }
}
function extractStrings(document) {
    const text = document.getText();
    const strings = [];
    // Match single, double, and backtick quoted strings
    const stringRegex = /(['"`])(?:(?!\1|\\).|\\.)*\1/g;
    let match;
    while ((match = stringRegex.exec(text)) !== null) {
        const fullMatch = match[0];
        const quote = match[1];
        const value = fullMatch.slice(1, -1); // Remove quotes
        // Skip template literals with expressions
        if (quote === '`' && value.includes('${'))
            continue;
        const startPos = document.positionAt(match.index + 1);
        const endPos = document.positionAt(match.index + fullMatch.length - 1);
        strings.push({
            value: unescapeString(value),
            range: new vscode.Range(startPos, endPos)
        });
    }
    return strings;
}
function unescapeString(s) {
    return s
        .replace(/\\n/g, '\n')
        .replace(/\\r/g, '\r')
        .replace(/\\t/g, '\t')
        .replace(/\\'/g, "'")
        .replace(/\\"/g, '"')
        .replace(/\\\\/g, '\\');
}
// ============================================================================
// DECORATIONS
// ============================================================================
const validDecorationType = vscode.window.createTextEditorDecorationType({
    after: {
        margin: '0 0 0 0.5em',
        color: new vscode.ThemeColor('testing.iconPassed'),
    }
});
const invalidDecorationType = vscode.window.createTextEditorDecorationType({
    after: {
        margin: '0 0 0 0.5em',
        color: new vscode.ThemeColor('testing.iconFailed'),
    },
    backgroundColor: new vscode.ThemeColor('inputValidation.errorBackground'),
    borderRadius: '2px'
});
function createDecorations(results) {
    const valid = [];
    const invalid = [];
    for (const result of results) {
        const label = TYPE_LABELS[result.type];
        const icon = result.isValid ? '✓' : '✗';
        const decoration = {
            range: result.range,
            hoverMessage: new vscode.MarkdownString(`**${label}**: ${result.isValid ? '✅ Valid' : '❌ Invalid'}\n\n` +
                `\`${result.value}\`\n\n` +
                result.message),
            renderOptions: {
                after: {
                    contentText: `${icon} ${label}`,
                    fontStyle: 'italic',
                    fontWeight: result.isValid ? 'normal' : 'bold'
                }
            }
        };
        if (result.isValid) {
            valid.push(decoration);
        }
        else {
            invalid.push(decoration);
        }
    }
    return { valid, invalid };
}
// ============================================================================
// CODELENS PROVIDER
// ============================================================================
class ValidatorCodeLensProvider {
    _onDidChangeCodeLenses = new vscode.EventEmitter();
    onDidChangeCodeLenses = this._onDidChangeCodeLenses.event;
    refresh() {
        this._onDidChangeCodeLenses.fire();
    }
    provideCodeLenses(document) {
        const config = vscode.workspace.getConfiguration('validatorLens');
        if (!config.get('enabled', true))
            return [];
        if (!config.get('showCodeLens', false))
            return [];
        const results = validateDocument(document);
        const invalidResults = results.filter(r => !r.isValid);
        if (invalidResults.length === 0)
            return [];
        return invalidResults.map(result => {
            const label = TYPE_LABELS[result.type];
            return new vscode.CodeLens(result.range, {
                title: `⚠️ Invalid ${label}`,
                command: 'validatorLens.validateSelection',
                arguments: [result]
            });
        });
    }
}
// ============================================================================
// DIAGNOSTICS
// ============================================================================
const diagnosticCollection = vscode.languages.createDiagnosticCollection('validatorLens');
function updateDiagnostics(document, results) {
    const diagnostics = [];
    for (const result of results.filter(r => !r.isValid)) {
        const diagnostic = new vscode.Diagnostic(result.range, `Invalid ${TYPE_LABELS[result.type]}: ${result.message}`, vscode.DiagnosticSeverity.Warning);
        diagnostic.source = 'Validator Lens';
        diagnostic.code = result.type;
        diagnostics.push(diagnostic);
    }
    diagnosticCollection.set(document.uri, diagnostics);
}
// ============================================================================
// MAIN VALIDATION
// ============================================================================
function validateDocument(document) {
    const config = vscode.workspace.getConfiguration('validatorLens');
    const minLength = config.get('minStringLength', 5);
    const maxValidations = config.get('maxValidationsPerFile', 200);
    const strings = extractStrings(document);
    const results = [];
    for (const str of strings) {
        if (results.length >= maxValidations)
            break;
        if (str.value.length < minLength)
            continue;
        const type = detectType(str.value);
        if (!type)
            continue;
        if (!isTypeEnabled(config, type))
            continue;
        const isValid = validate(type, str.value);
        const message = isValid
            ? `This ${TYPE_LABELS[type]} is properly formatted.`
            : `This ${TYPE_LABELS[type]} appears to be malformed.`;
        results.push({
            type,
            value: str.value,
            isValid,
            range: str.range,
            message
        });
    }
    return results;
}
function updateDecorations(editor) {
    const config = vscode.workspace.getConfiguration('validatorLens');
    if (!config.get('enabled', true)) {
        editor.setDecorations(validDecorationType, []);
        editor.setDecorations(invalidDecorationType, []);
        return;
    }
    if (!config.get('showInlineHints', true)) {
        editor.setDecorations(validDecorationType, []);
        editor.setDecorations(invalidDecorationType, []);
        return;
    }
    const results = validateDocument(editor.document);
    const { valid, invalid } = createDecorations(results);
    editor.setDecorations(validDecorationType, valid);
    editor.setDecorations(invalidDecorationType, invalid);
    updateDiagnostics(editor.document, results);
}
// ============================================================================
// EXTENSION ACTIVATION
// ============================================================================
let debounceTimer;
function activate(context) {
    const codeLensProvider = new ValidatorCodeLensProvider();
    // Register CodeLens provider
    context.subscriptions.push(vscode.languages.registerCodeLensProvider({ scheme: 'file' }, codeLensProvider));
    // Toggle command
    context.subscriptions.push(vscode.commands.registerCommand('validatorLens.toggleEnabled', async () => {
        const config = vscode.workspace.getConfiguration('validatorLens');
        const current = config.get('enabled', true);
        await config.update('enabled', !current, vscode.ConfigurationTarget.Global);
        vscode.window.showInformationMessage(`Validator Lens ${!current ? 'enabled' : 'disabled'}`);
    }));
    // Validate selection command
    context.subscriptions.push(vscode.commands.registerCommand('validatorLens.validateSelection', () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor)
            return;
        const selection = editor.selection;
        const text = editor.document.getText(selection);
        if (!text) {
            vscode.window.showWarningMessage('No text selected');
            return;
        }
        const type = detectType(text);
        if (!type) {
            vscode.window.showInformationMessage('No recognizable format detected');
            return;
        }
        const isValid = validate(type, text);
        const label = TYPE_LABELS[type];
        if (isValid) {
            vscode.window.showInformationMessage(`✅ Valid ${label}`);
        }
        else {
            vscode.window.showWarningMessage(`❌ Invalid ${label}`);
        }
    }));
    // Show all issues command
    context.subscriptions.push(vscode.commands.registerCommand('validatorLens.showAllIssues', () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor)
            return;
        const results = validateDocument(editor.document);
        const invalid = results.filter(r => !r.isValid);
        if (invalid.length === 0) {
            vscode.window.showInformationMessage('No validation issues found');
            return;
        }
        const items = invalid.map(r => ({
            label: `${TYPE_LABELS[r.type]}: ${r.value.slice(0, 50)}${r.value.length > 50 ? '...' : ''}`,
            description: `Line ${r.range.start.line + 1}`,
            result: r
        }));
        vscode.window.showQuickPick(items, {
            placeHolder: `${invalid.length} validation issue(s) found`
        }).then(item => {
            if (item) {
                editor.selection = new vscode.Selection(item.result.range.start, item.result.range.end);
                editor.revealRange(item.result.range);
            }
        });
    }));
    // Copy valid value command
    context.subscriptions.push(vscode.commands.registerCommand('validatorLens.copyValidValue', () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor)
            return;
        const selection = editor.selection;
        const text = editor.document.getText(selection);
        if (!text) {
            vscode.window.showWarningMessage('No text selected');
            return;
        }
        vscode.env.clipboard.writeText(text);
        vscode.window.showInformationMessage('Value copied to clipboard');
    }));
    // Update on active editor change
    context.subscriptions.push(vscode.window.onDidChangeActiveTextEditor(editor => {
        if (editor) {
            updateDecorations(editor);
        }
    }));
    // Update on document change (debounced)
    context.subscriptions.push(vscode.workspace.onDidChangeTextDocument(event => {
        const editor = vscode.window.activeTextEditor;
        if (editor && event.document === editor.document) {
            if (debounceTimer) {
                clearTimeout(debounceTimer);
            }
            debounceTimer = setTimeout(() => {
                updateDecorations(editor);
                codeLensProvider.refresh();
            }, 500);
        }
    }));
    // Update on config change
    context.subscriptions.push(vscode.workspace.onDidChangeConfiguration(event => {
        if (event.affectsConfiguration('validatorLens')) {
            const editor = vscode.window.activeTextEditor;
            if (editor) {
                updateDecorations(editor);
                codeLensProvider.refresh();
            }
        }
    }));
    // Initial update
    if (vscode.window.activeTextEditor) {
        updateDecorations(vscode.window.activeTextEditor);
    }
    context.subscriptions.push(diagnosticCollection);
}
function deactivate() {
    diagnosticCollection.dispose();
}
//# sourceMappingURL=extension.js.map