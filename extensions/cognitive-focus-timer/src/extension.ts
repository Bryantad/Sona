import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';

// ============================================================================
// TYPES
// ============================================================================

type TimerPhase = 'focus' | 'shortBreak' | 'longBreak' | 'idle';

interface SessionLog {
    date: string;
    startTime: string;
    endTime: string;
    phase: TimerPhase;
    durationMinutes: number;
    completed: boolean;
}

interface DailyStats {
    date: string;
    focusSessions: number;
    totalFocusMinutes: number;
    totalBreakMinutes: number;
    streak: number;
    goalReached: boolean;
}

// ============================================================================
// TIMER STATE
// ============================================================================

class FocusTimerState {
    phase: TimerPhase = 'idle';
    remainingSeconds: number = 0;
    totalSeconds: number = 0;
    isPaused: boolean = false;
    sessionCount: number = 0;
    currentStreak: number = 0;
    todayFocusSessions: number = 0;
    todayFocusMinutes: number = 0;
    sessionStartTime: Date | null = null;
    
    private intervalId: NodeJS.Timeout | null = null;
    private statusBarItem: vscode.StatusBarItem;
    private context: vscode.ExtensionContext;
    private onTick: () => void;
    private onPhaseComplete: (phase: TimerPhase) => void;

    constructor(
        statusBarItem: vscode.StatusBarItem,
        context: vscode.ExtensionContext,
        onTick: () => void,
        onPhaseComplete: (phase: TimerPhase) => void
    ) {
        this.statusBarItem = statusBarItem;
        this.context = context;
        this.onTick = onTick;
        this.onPhaseComplete = onPhaseComplete;
        this.loadState();
    }

    private loadState(): void {
        const today = new Date().toISOString().split('T')[0];
        const savedDate = this.context.globalState.get<string>('focusTimer.lastDate');
        
        if (savedDate === today) {
            this.todayFocusSessions = this.context.globalState.get<number>('focusTimer.todaySessions', 0);
            this.todayFocusMinutes = this.context.globalState.get<number>('focusTimer.todayMinutes', 0);
            this.currentStreak = this.context.globalState.get<number>('focusTimer.streak', 0);
        } else {
            // New day - check if streak continues
            const lastStreak = this.context.globalState.get<number>('focusTimer.streak', 0);
            const lastGoalReached = this.context.globalState.get<boolean>('focusTimer.lastGoalReached', false);
            
            if (lastGoalReached && savedDate) {
                const lastDate = new Date(savedDate);
                const diff = Math.floor((new Date().getTime() - lastDate.getTime()) / (1000 * 60 * 60 * 24));
                this.currentStreak = diff <= 1 ? lastStreak : 0;
            } else {
                this.currentStreak = 0;
            }
            
            this.todayFocusSessions = 0;
            this.todayFocusMinutes = 0;
            this.context.globalState.update('focusTimer.lastDate', today);
        }
    }

    private saveState(): void {
        const today = new Date().toISOString().split('T')[0];
        const config = vscode.workspace.getConfiguration('focusTimer');
        const dailyGoal = config.get<number>('dailyGoal', 8);
        
        this.context.globalState.update('focusTimer.lastDate', today);
        this.context.globalState.update('focusTimer.todaySessions', this.todayFocusSessions);
        this.context.globalState.update('focusTimer.todayMinutes', this.todayFocusMinutes);
        this.context.globalState.update('focusTimer.streak', this.currentStreak);
        this.context.globalState.update('focusTimer.lastGoalReached', this.todayFocusSessions >= dailyGoal);
    }

    startFocus(): void {
        const config = vscode.workspace.getConfiguration('focusTimer');
        const duration = config.get<number>('focusDuration', 25);
        
        this.phase = 'focus';
        this.totalSeconds = duration * 60;
        this.remainingSeconds = this.totalSeconds;
        this.isPaused = false;
        this.sessionStartTime = new Date();
        this.startInterval();
    }

    startShortBreak(): void {
        const config = vscode.workspace.getConfiguration('focusTimer');
        const duration = config.get<number>('shortBreakDuration', 5);
        
        this.phase = 'shortBreak';
        this.totalSeconds = duration * 60;
        this.remainingSeconds = this.totalSeconds;
        this.isPaused = false;
        this.sessionStartTime = new Date();
        this.startInterval();
    }

    startLongBreak(): void {
        const config = vscode.workspace.getConfiguration('focusTimer');
        const duration = config.get<number>('longBreakDuration', 15);
        
        this.phase = 'longBreak';
        this.totalSeconds = duration * 60;
        this.remainingSeconds = this.totalSeconds;
        this.isPaused = false;
        this.sessionStartTime = new Date();
        this.startInterval();
    }

    pause(): void {
        this.isPaused = true;
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
    }

    resume(): void {
        if (this.isPaused && this.phase !== 'idle') {
            this.isPaused = false;
            this.startInterval();
        }
    }

    stop(): void {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
        this.phase = 'idle';
        this.remainingSeconds = 0;
        this.totalSeconds = 0;
        this.isPaused = false;
        this.sessionStartTime = null;
    }

    skip(): void {
        if (this.phase !== 'idle') {
            const completedPhase = this.phase;
            this.stop();
            this.onPhaseComplete(completedPhase);
        }
    }

    private startInterval(): void {
        if (this.intervalId) {
            clearInterval(this.intervalId);
        }

        this.intervalId = setInterval(() => {
            if (!this.isPaused) {
                this.remainingSeconds--;
                this.onTick();

                if (this.remainingSeconds <= 0) {
                    this.completePhase();
                }
            }
        }, 1000);
    }

    private completePhase(): void {
        const completedPhase = this.phase;
        
        if (completedPhase === 'focus') {
            this.sessionCount++;
            this.todayFocusSessions++;
            this.todayFocusMinutes += Math.floor(this.totalSeconds / 60);
            
            const config = vscode.workspace.getConfiguration('focusTimer');
            const dailyGoal = config.get<number>('dailyGoal', 8);
            
            if (this.todayFocusSessions >= dailyGoal && this.todayFocusSessions === dailyGoal) {
                this.currentStreak++;
            }
            
            this.saveState();
            this.logSession(completedPhase, true);
        }

        this.stop();
        this.onPhaseComplete(completedPhase);
    }

    private logSession(phase: TimerPhase, completed: boolean): void {
        const config = vscode.workspace.getConfiguration('focusTimer');
        if (!config.get<boolean>('logSessionsToFile', true)) {
            return;
        }

        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        if (!workspaceFolder) return;

        const logDir = path.join(workspaceFolder.uri.fsPath, '.focus-timer');
        const logFile = path.join(logDir, 'sessions.json');

        try {
            if (!fs.existsSync(logDir)) {
                fs.mkdirSync(logDir, { recursive: true });
            }

            let sessions: SessionLog[] = [];
            if (fs.existsSync(logFile)) {
                sessions = JSON.parse(fs.readFileSync(logFile, 'utf-8'));
            }

            const now = new Date();
            sessions.push({
                date: now.toISOString().split('T')[0],
                startTime: this.sessionStartTime?.toISOString() || now.toISOString(),
                endTime: now.toISOString(),
                phase,
                durationMinutes: Math.floor(this.totalSeconds / 60),
                completed
            });

            // Keep last 1000 sessions
            if (sessions.length > 1000) {
                sessions = sessions.slice(-1000);
            }

            fs.writeFileSync(logFile, JSON.stringify(sessions, null, 2));
        } catch {
            // Ignore logging errors
        }
    }

    getProgress(): number {
        if (this.totalSeconds === 0) return 0;
        return 1 - (this.remainingSeconds / this.totalSeconds);
    }

    formatTime(): string {
        const minutes = Math.floor(this.remainingSeconds / 60);
        const seconds = this.remainingSeconds % 60;
        return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }
}

// ============================================================================
// STATUS BAR
// ============================================================================

function getPhaseIcon(phase: TimerPhase, isPaused: boolean): string {
    if (isPaused) return '$(debug-pause)';
    switch (phase) {
        case 'focus': return '$(flame)';
        case 'shortBreak': return '$(coffee)';
        case 'longBreak': return '$(heart)';
        default: return '$(clock)';
    }
}

function getPhaseLabel(phase: TimerPhase): string {
    switch (phase) {
        case 'focus': return 'Focus';
        case 'shortBreak': return 'Break';
        case 'longBreak': return 'Long Break';
        default: return 'Ready';
    }
}

function updateStatusBar(statusBar: vscode.StatusBarItem, state: FocusTimerState): void {
    const icon = getPhaseIcon(state.phase, state.isPaused);
    
    if (state.phase === 'idle') {
        statusBar.text = `${icon} Focus Timer`;
        statusBar.tooltip = new vscode.MarkdownString(
            `**Focus Timer**\n\n` +
            `Today: ${state.todayFocusSessions} sessions (${state.todayFocusMinutes} min)\n\n` +
            `🔥 Streak: ${state.currentStreak} days\n\n` +
            `Click to start a focus session`
        );
        statusBar.backgroundColor = undefined;
    } else {
        const time = state.formatTime();
        const label = getPhaseLabel(state.phase);
        const pauseIndicator = state.isPaused ? ' [PAUSED]' : '';
        
        statusBar.text = `${icon} ${label}: ${time}${pauseIndicator}`;
        
        const progress = Math.round(state.getProgress() * 100);
        statusBar.tooltip = new vscode.MarkdownString(
            `**${label}**${pauseIndicator}\n\n` +
            `Progress: ${progress}%\n\n` +
            `Session ${state.sessionCount + 1} | ` +
            `Today: ${state.todayFocusSessions} sessions\n\n` +
            `🔥 Streak: ${state.currentStreak} days`
        );

        if (state.phase === 'focus' && !state.isPaused) {
            statusBar.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');
        } else if (state.phase !== 'focus' && !state.isPaused) {
            statusBar.backgroundColor = new vscode.ThemeColor('statusBarItem.prominentBackground');
        } else {
            statusBar.backgroundColor = undefined;
        }
    }
    
    statusBar.command = state.phase === 'idle' ? 'focusTimer.start' : 'focusTimer.showStats';
    statusBar.show();
}

// ============================================================================
// NOTIFICATIONS
// ============================================================================

async function showPhaseCompleteNotification(
    phase: TimerPhase,
    state: FocusTimerState,
    onNext: (action: 'focus' | 'shortBreak' | 'longBreak') => void
): Promise<void> {
    const config = vscode.workspace.getConfiguration('focusTimer');
    
    if (!config.get<boolean>('showNotifications', true)) {
        return;
    }

    const sessionsBeforeLong = config.get<number>('sessionsBeforeLongBreak', 4);
    
    if (phase === 'focus') {
        const isLongBreak = state.sessionCount % sessionsBeforeLong === 0;
        const breakType = isLongBreak ? 'long break' : 'short break';
        const breakDuration = isLongBreak 
            ? config.get<number>('longBreakDuration', 15)
            : config.get<number>('shortBreakDuration', 5);

        const message = `🎉 Focus session complete! Time for a ${breakType} (${breakDuration} min).`;
        
        if (config.get<boolean>('autoStartBreaks', true)) {
            vscode.window.showInformationMessage(message);
            onNext(isLongBreak ? 'longBreak' : 'shortBreak');
        } else {
            const action = await vscode.window.showInformationMessage(
                message,
                'Start Break',
                'Skip'
            );
            if (action === 'Start Break') {
                onNext(isLongBreak ? 'longBreak' : 'shortBreak');
            }
        }
    } else {
        const message = '☕ Break complete! Ready to focus?';
        
        if (config.get<boolean>('autoStartFocus', false)) {
            vscode.window.showInformationMessage(message);
            onNext('focus');
        } else {
            const action = await vscode.window.showInformationMessage(
                message,
                'Start Focus',
                'Skip'
            );
            if (action === 'Start Focus') {
                onNext('focus');
            }
        }
    }
}

// ============================================================================
// STATS PANEL
// ============================================================================

async function showStatsPanel(context: vscode.ExtensionContext, state: FocusTimerState): Promise<void> {
    const config = vscode.workspace.getConfiguration('focusTimer');
    const dailyGoal = config.get<number>('dailyGoal', 8);
    const progress = Math.min(100, Math.round((state.todayFocusSessions / dailyGoal) * 100));
    const progressBar = '█'.repeat(Math.floor(progress / 10)) + '░'.repeat(10 - Math.floor(progress / 10));

    const panel = vscode.window.createWebviewPanel(
        'focusTimerStats',
        'Focus Timer Stats',
        vscode.ViewColumn.One,
        { enableScripts: true }
    );

    panel.webview.html = `<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {
            font-family: var(--vscode-font-family);
            color: var(--vscode-foreground);
            background: var(--vscode-editor-background);
            padding: 30px;
            line-height: 1.6;
        }
        .header {
            text-align: center;
            margin-bottom: 40px;
        }
        .header h1 {
            margin: 0;
            font-size: 2em;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        .stat-card {
            background: var(--vscode-editor-inactiveSelectionBackground);
            border-radius: 12px;
            padding: 24px;
            text-align: center;
        }
        .stat-value {
            font-size: 3em;
            font-weight: bold;
            color: var(--vscode-textLink-foreground);
        }
        .stat-label {
            color: var(--vscode-descriptionForeground);
            margin-top: 8px;
        }
        .progress-section {
            margin-bottom: 40px;
        }
        .progress-section h2 {
            margin-bottom: 16px;
        }
        .progress-bar {
            font-family: monospace;
            font-size: 1.5em;
            letter-spacing: 2px;
        }
        .progress-text {
            color: var(--vscode-descriptionForeground);
            margin-top: 8px;
        }
        .streak-section {
            text-align: center;
            padding: 30px;
            background: linear-gradient(135deg, var(--vscode-editor-inactiveSelectionBackground), transparent);
            border-radius: 12px;
        }
        .streak-value {
            font-size: 4em;
            margin-bottom: 10px;
        }
        .tips {
            margin-top: 40px;
            padding: 20px;
            background: var(--vscode-textBlockQuote-background);
            border-radius: 8px;
            border-left: 4px solid var(--vscode-textLink-foreground);
        }
        .tips h3 {
            margin-top: 0;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🧠 Focus Timer</h1>
        <p>Today's Progress</p>
    </div>

    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-value">${state.todayFocusSessions}</div>
            <div class="stat-label">Focus Sessions</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${state.todayFocusMinutes}</div>
            <div class="stat-label">Minutes Focused</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${Math.floor(state.todayFocusMinutes / 60)}h ${state.todayFocusMinutes % 60}m</div>
            <div class="stat-label">Total Time</div>
        </div>
    </div>

    <div class="progress-section">
        <h2>Daily Goal Progress</h2>
        <div class="progress-bar">${progressBar}</div>
        <div class="progress-text">${state.todayFocusSessions} / ${dailyGoal} sessions (${progress}%)</div>
    </div>

    <div class="streak-section">
        <div class="streak-value">🔥 ${state.currentStreak}</div>
        <div>Day Streak</div>
        ${state.currentStreak > 0 ? `<p style="color: var(--vscode-textLink-foreground);">Keep it going!</p>` : '<p>Complete your daily goal to start a streak!</p>'}
    </div>

    <div class="tips">
        <h3>💡 Focus Tips</h3>
        <ul>
            <li>During focus time, try to avoid checking messages</li>
            <li>Keep water nearby to stay hydrated</li>
            <li>Stand up and stretch during breaks</li>
            <li>If you finish a task early, review your work</li>
        </ul>
    </div>
</body>
</html>`;
}

// ============================================================================
// HISTORY PANEL
// ============================================================================

async function showHistoryPanel(): Promise<void> {
    const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
    if (!workspaceFolder) {
        vscode.window.showWarningMessage('No workspace folder found');
        return;
    }

    const logFile = path.join(workspaceFolder.uri.fsPath, '.focus-timer', 'sessions.json');
    
    if (!fs.existsSync(logFile)) {
        vscode.window.showInformationMessage('No session history found yet. Start a focus session to begin tracking!');
        return;
    }

    try {
        const sessions: SessionLog[] = JSON.parse(fs.readFileSync(logFile, 'utf-8'));
        
        // Group by date
        const byDate = new Map<string, SessionLog[]>();
        for (const session of sessions) {
            const existing = byDate.get(session.date) || [];
            existing.push(session);
            byDate.set(session.date, existing);
        }

        const dates = Array.from(byDate.keys()).sort().reverse().slice(0, 14);
        
        const rows = dates.map(date => {
            const daySessions = byDate.get(date) || [];
            const focusSessions = daySessions.filter(s => s.phase === 'focus' && s.completed);
            const totalMinutes = focusSessions.reduce((sum, s) => sum + s.durationMinutes, 0);
            return `
                <tr>
                    <td>${date}</td>
                    <td>${focusSessions.length}</td>
                    <td>${totalMinutes} min</td>
                    <td>${Math.floor(totalMinutes / 60)}h ${totalMinutes % 60}m</td>
                </tr>
            `;
        }).join('');

        const panel = vscode.window.createWebviewPanel(
            'focusTimerHistory',
            'Focus Timer History',
            vscode.ViewColumn.One,
            {}
        );

        panel.webview.html = `<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {
            font-family: var(--vscode-font-family);
            color: var(--vscode-foreground);
            background: var(--vscode-editor-background);
            padding: 30px;
        }
        h1 { margin-bottom: 30px; }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            text-align: left;
            padding: 12px;
            border-bottom: 1px solid var(--vscode-panel-border);
        }
        th {
            color: var(--vscode-descriptionForeground);
            font-weight: 600;
        }
        tr:hover {
            background: var(--vscode-list-hoverBackground);
        }
    </style>
</head>
<body>
    <h1>📊 Session History (Last 14 Days)</h1>
    <table>
        <thead>
            <tr>
                <th>Date</th>
                <th>Sessions</th>
                <th>Minutes</th>
                <th>Total</th>
            </tr>
        </thead>
        <tbody>
            ${rows || '<tr><td colspan="4">No sessions recorded yet</td></tr>'}
        </tbody>
    </table>
</body>
</html>`;
    } catch {
        vscode.window.showErrorMessage('Failed to load session history');
    }
}

// ============================================================================
// EXTENSION ACTIVATION
// ============================================================================

export function activate(context: vscode.ExtensionContext): void {
    // Create status bar item
    const statusBarItem = vscode.window.createStatusBarItem(
        vscode.StatusBarAlignment.Right,
        100
    );

    // Initialize state
    const state = new FocusTimerState(
        statusBarItem,
        context,
        () => updateStatusBar(statusBarItem, state),
        (phase) => {
            updateStatusBar(statusBarItem, state);
            showPhaseCompleteNotification(phase, state, (action) => {
                switch (action) {
                    case 'focus': state.startFocus(); break;
                    case 'shortBreak': state.startShortBreak(); break;
                    case 'longBreak': state.startLongBreak(); break;
                }
                updateStatusBar(statusBarItem, state);
            });
        }
    );

    // Initial status bar update
    updateStatusBar(statusBarItem, state);

    // Register commands
    context.subscriptions.push(
        vscode.commands.registerCommand('focusTimer.start', () => {
            state.startFocus();
            updateStatusBar(statusBarItem, state);
            vscode.window.showInformationMessage('🔥 Focus session started! Stay focused.');
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('focusTimer.pause', () => {
            if (state.isPaused) {
                state.resume();
                vscode.window.showInformationMessage('▶️ Timer resumed');
            } else {
                state.pause();
                vscode.window.showInformationMessage('⏸️ Timer paused');
            }
            updateStatusBar(statusBarItem, state);
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('focusTimer.stop', () => {
            state.stop();
            updateStatusBar(statusBarItem, state);
            vscode.window.showInformationMessage('⏹️ Session stopped');
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('focusTimer.skip', () => {
            state.skip();
            updateStatusBar(statusBarItem, state);
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('focusTimer.showStats', () => {
            showStatsPanel(context, state);
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('focusTimer.showHistory', () => {
            showHistoryPanel();
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('focusTimer.resetStreak', async () => {
            const confirm = await vscode.window.showWarningMessage(
                'Reset your streak to 0?',
                { modal: true },
                'Reset'
            );
            if (confirm === 'Reset') {
                state.currentStreak = 0;
                context.globalState.update('focusTimer.streak', 0);
                updateStatusBar(statusBarItem, state);
                vscode.window.showInformationMessage('Streak reset');
            }
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('focusTimer.configure', () => {
            vscode.commands.executeCommand('workbench.action.openSettings', 'focusTimer');
        })
    );

    context.subscriptions.push(statusBarItem);
}

export function deactivate(): void {}
