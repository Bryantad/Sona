import * as vscode from 'vscode';

// ============================================================================
// TYPES
// ============================================================================

type ValidationType = 
    | 'email' 
    | 'url' 
    | 'uuid' 
    | 'ipv4' 
    | 'ipv6' 
    | 'date' 
    | 'phone' 
    | 'creditCard' 
    | 'hexColor'
    | 'json';

interface ValidationResult {
    type: ValidationType;
    value: string;
    isValid: boolean;
    range: vscode.Range;
    message: string;
}

// ============================================================================
// VALIDATORS
// ============================================================================

const PATTERNS: Record<ValidationType, RegExp> = {
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

const TYPE_LABELS: Record<ValidationType, string> = {
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

function detectType(value: string): ValidationType | null {
    // Order matters - more specific patterns first
    if (PATTERNS.uuid.test(value)) return 'uuid';
    if (PATTERNS.hexColor.test(value)) return 'hexColor';
    if (PATTERNS.ipv4.test(value)) return 'ipv4';
    if (PATTERNS.ipv6.test(value)) return 'ipv6';
    if (PATTERNS.email.test(value)) return 'email';
    if (PATTERNS.date.test(value)) return 'date';
    if (PATTERNS.url.test(value)) return 'url';
    if (PATTERNS.phone.test(value)) return 'phone';
    if (PATTERNS.creditCard.test(value.replace(/[\s-]/g, ''))) return 'creditCard';
    if (PATTERNS.json.test(value)) return 'json';
    return null;
}

function validateEmail(value: string): boolean {
    return PATTERNS.email.test(value);
}

function validateUrl(value: string): boolean {
    try {
        new URL(value.startsWith('http') ? value : `https://${value}`);
        return true;
    } catch {
        return false;
    }
}

function validateUuid(value: string): boolean {
    return PATTERNS.uuid.test(value);
}

function validateIpv4(value: string): boolean {
    if (!PATTERNS.ipv4.test(value)) return false;
    const parts = value.split('.').map(Number);
    return parts.every(p => p >= 0 && p <= 255);
}

function validateIpv6(value: string): boolean {
    return PATTERNS.ipv6.test(value);
}

function validateDate(value: string): boolean {
    if (!PATTERNS.date.test(value)) return false;
    const date = new Date(value);
    return !isNaN(date.getTime());
}

function validatePhone(value: string): boolean {
    const digits = value.replace(/\D/g, '');
    return digits.length >= 7 && digits.length <= 15;
}

function validateCreditCard(value: string): boolean {
    const digits = value.replace(/[\s-]/g, '');
    if (!/^\d{13,19}$/.test(digits)) return false;
    
    // Luhn algorithm
    let sum = 0;
    let isEven = false;
    for (let i = digits.length - 1; i >= 0; i--) {
        let digit = parseInt(digits[i], 10);
        if (isEven) {
            digit *= 2;
            if (digit > 9) digit -= 9;
        }
        sum += digit;
        isEven = !isEven;
    }
    return sum % 10 === 0;
}

function validateHexColor(value: string): boolean {
    return PATTERNS.hexColor.test(value);
}

function validateJson(value: string): boolean {
    try {
        JSON.parse(value);
        return true;
    } catch {
        return false;
    }
}

function validate(type: ValidationType, value: string): boolean {
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

function isTypeEnabled(config: vscode.WorkspaceConfiguration, type: ValidationType): boolean {
    switch (type) {
        case 'email': return config.get<boolean>('validateEmails', true);
        case 'url': return config.get<boolean>('validateUrls', true);
        case 'uuid': return config.get<boolean>('validateUuids', true);
        case 'ipv4':
        case 'ipv6': return config.get<boolean>('validateIpAddresses', true);
        case 'date': return config.get<boolean>('validateDates', true);
        case 'phone': return config.get<boolean>('validatePhoneNumbers', true);
        case 'creditCard': return config.get<boolean>('validateCreditCards', false);
        case 'hexColor': return config.get<boolean>('validateHexColors', true);
        case 'json': return config.get<boolean>('validateJson', true);
    }
}

// ============================================================================
// STRING EXTRACTION
// ============================================================================

interface StringLiteral {
    value: string;
    range: vscode.Range;
}

function extractStrings(document: vscode.TextDocument): StringLiteral[] {
    const text = document.getText();
    const strings: StringLiteral[] = [];
    
    // Match single, double, and backtick quoted strings
    const stringRegex = /(['"`])(?:(?!\1|\\).|\\.)*\1/g;
    
    let match;
    while ((match = stringRegex.exec(text)) !== null) {
        const fullMatch = match[0];
        const quote = match[1];
        const value = fullMatch.slice(1, -1); // Remove quotes
        
        // Skip template literals with expressions
        if (quote === '`' && value.includes('${')) continue;
        
        const startPos = document.positionAt(match.index + 1);
        const endPos = document.positionAt(match.index + fullMatch.length - 1);
        
        strings.push({
            value: unescapeString(value),
            range: new vscode.Range(startPos, endPos)
        });
    }
    
    return strings;
}

function unescapeString(s: string): string {
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

function createDecorations(results: ValidationResult[]): {
    valid: vscode.DecorationOptions[];
    invalid: vscode.DecorationOptions[];
} {
    const valid: vscode.DecorationOptions[] = [];
    const invalid: vscode.DecorationOptions[] = [];

    for (const result of results) {
        const label = TYPE_LABELS[result.type];
        const icon = result.isValid ? '✓' : '✗';
        
        const decoration: vscode.DecorationOptions = {
            range: result.range,
            hoverMessage: new vscode.MarkdownString(
                `**${label}**: ${result.isValid ? '✅ Valid' : '❌ Invalid'}\n\n` +
                `\`${result.value}\`\n\n` +
                result.message
            ),
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
        } else {
            invalid.push(decoration);
        }
    }

    return { valid, invalid };
}

// ============================================================================
// CODELENS PROVIDER
// ============================================================================

class ValidatorCodeLensProvider implements vscode.CodeLensProvider {
    private _onDidChangeCodeLenses = new vscode.EventEmitter<void>();
    readonly onDidChangeCodeLenses = this._onDidChangeCodeLenses.event;

    refresh(): void {
        this._onDidChangeCodeLenses.fire();
    }

    provideCodeLenses(document: vscode.TextDocument): vscode.CodeLens[] {
        const config = vscode.workspace.getConfiguration('validatorLens');
        if (!config.get<boolean>('enabled', true)) return [];
        if (!config.get<boolean>('showCodeLens', false)) return [];

        const results = validateDocument(document);
        const invalidResults = results.filter(r => !r.isValid);

        if (invalidResults.length === 0) return [];

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

function updateDiagnostics(document: vscode.TextDocument, results: ValidationResult[]): void {
    const diagnostics: vscode.Diagnostic[] = [];

    for (const result of results.filter(r => !r.isValid)) {
        const diagnostic = new vscode.Diagnostic(
            result.range,
            `Invalid ${TYPE_LABELS[result.type]}: ${result.message}`,
            vscode.DiagnosticSeverity.Warning
        );
        diagnostic.source = 'Validator Lens';
        diagnostic.code = result.type;
        diagnostics.push(diagnostic);
    }

    diagnosticCollection.set(document.uri, diagnostics);
}

// ============================================================================
// MAIN VALIDATION
// ============================================================================

function validateDocument(document: vscode.TextDocument): ValidationResult[] {
    const config = vscode.workspace.getConfiguration('validatorLens');
    const minLength = config.get<number>('minStringLength', 5);
    const maxValidations = config.get<number>('maxValidationsPerFile', 200);

    const strings = extractStrings(document);
    const results: ValidationResult[] = [];

    for (const str of strings) {
        if (results.length >= maxValidations) break;
        if (str.value.length < minLength) continue;

        const type = detectType(str.value);
        if (!type) continue;
        if (!isTypeEnabled(config, type)) continue;

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

function updateDecorations(editor: vscode.TextEditor): void {
    const config = vscode.workspace.getConfiguration('validatorLens');
    if (!config.get<boolean>('enabled', true)) {
        editor.setDecorations(validDecorationType, []);
        editor.setDecorations(invalidDecorationType, []);
        return;
    }

    if (!config.get<boolean>('showInlineHints', true)) {
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

let debounceTimer: NodeJS.Timeout | undefined;

export function activate(context: vscode.ExtensionContext): void {
    const codeLensProvider = new ValidatorCodeLensProvider();

    // Register CodeLens provider
    context.subscriptions.push(
        vscode.languages.registerCodeLensProvider(
            { scheme: 'file' },
            codeLensProvider
        )
    );

    // Toggle command
    context.subscriptions.push(
        vscode.commands.registerCommand('validatorLens.toggleEnabled', async () => {
            const config = vscode.workspace.getConfiguration('validatorLens');
            const current = config.get<boolean>('enabled', true);
            await config.update('enabled', !current, vscode.ConfigurationTarget.Global);
            vscode.window.showInformationMessage(
                `Validator Lens ${!current ? 'enabled' : 'disabled'}`
            );
        })
    );

    // Validate selection command
    context.subscriptions.push(
        vscode.commands.registerCommand('validatorLens.validateSelection', () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) return;

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
            } else {
                vscode.window.showWarningMessage(`❌ Invalid ${label}`);
            }
        })
    );

    // Show all issues command
    context.subscriptions.push(
        vscode.commands.registerCommand('validatorLens.showAllIssues', () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) return;

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
                    editor.selection = new vscode.Selection(
                        item.result.range.start,
                        item.result.range.end
                    );
                    editor.revealRange(item.result.range);
                }
            });
        })
    );

    // Copy valid value command
    context.subscriptions.push(
        vscode.commands.registerCommand('validatorLens.copyValidValue', () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) return;

            const selection = editor.selection;
            const text = editor.document.getText(selection);

            if (!text) {
                vscode.window.showWarningMessage('No text selected');
                return;
            }

            vscode.env.clipboard.writeText(text);
            vscode.window.showInformationMessage('Value copied to clipboard');
        })
    );

    // Update on active editor change
    context.subscriptions.push(
        vscode.window.onDidChangeActiveTextEditor(editor => {
            if (editor) {
                updateDecorations(editor);
            }
        })
    );

    // Update on document change (debounced)
    context.subscriptions.push(
        vscode.workspace.onDidChangeTextDocument(event => {
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
        })
    );

    // Update on config change
    context.subscriptions.push(
        vscode.workspace.onDidChangeConfiguration(event => {
            if (event.affectsConfiguration('validatorLens')) {
                const editor = vscode.window.activeTextEditor;
                if (editor) {
                    updateDecorations(editor);
                    codeLensProvider.refresh();
                }
            }
        })
    );

    // Initial update
    if (vscode.window.activeTextEditor) {
        updateDecorations(vscode.window.activeTextEditor);
    }

    context.subscriptions.push(diagnosticCollection);
}

export function deactivate(): void {
    diagnosticCollection.dispose();
}
