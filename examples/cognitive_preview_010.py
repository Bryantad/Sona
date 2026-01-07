import time

class _SonaCognitiveRuntime:
    def __init__(self):
        self.working_memory = {}
        self.focus_sessions = []
        self.intent_stack = []
        self.decision_log = []
        self.scope_stack = []
        self.trace_enabled = False
        self.trace_log = []
        self.profile = None
        self.last_analysis = None
        self.lint_warnings = []

    def _record_trace(self, event_type, payload):
        if not self.trace_enabled:
            return
        self.trace_log.append({
            'type': event_type,
            'payload': payload,
            'timestamp': time.time(),
        })

    def _basic_analysis(self, task, context):
        context_text = str(context or "")
        length = len(context_text)
        if length < 200:
            load = "low"
        elif length < 800:
            load = "medium"
        else:
            load = "high"
        suggestions = []
        if load != "low":
            suggestions.append("Break work into smaller steps")
        if load == "high":
            suggestions.append("Schedule a short break and resume with a plan")
        return {
            'task': task or "",
            'cognitive_load': load,
            'context_preview': context_text[:160],
            'suggestions': suggestions,
        }

    def _compute_intent_overlap(self, goal, activity):
        if not goal or not activity:
            return 1.0 if not goal else 0.0
        goal_tokens = set(str(goal).lower().split())
        act_tokens = set(str(activity).lower().split())
        if not goal_tokens:
            return 0.0
        return len(goal_tokens & act_tokens) / len(goal_tokens)

    def check_cognitive_load(self, params):
        task = str(params.get('task') or params.get('arg0') or "")
        context = params.get('context') or params.get('code') or params.get('arg1') or ""
        analysis = self._basic_analysis(task, context)
        intent = self.intent_stack[-1] if self.intent_stack else {}
        goal = str(intent.get('goal') or intent.get('intent') or intent.get('arg0') or "")
        drift_score = self._compute_intent_overlap(goal, str(task or context))
        analysis['intent_goal'] = goal
        analysis['intent_drift_score'] = drift_score
        analysis['intent_drift'] = drift_score < 0.4 if goal else False
        analysis['confidence'] = 'high' if analysis['cognitive_load'] == 'low' else 'medium'
        self.last_analysis = analysis
        self._record_trace('cognitive_check', analysis)
        return analysis

    def configure_focus_mode(self, params):
        action = params.get('action', 'start')
        description = str(params.get('task') or params.get('mode') or params.get('arg0') or 'focus')
        minutes = params.get('minutes') or params.get('duration') or params.get('arg1') or 25
        try:
            minutes = int(minutes)
        except Exception:
            minutes = 25
        if action == 'status':
            return {
                'status': 'ok',
                'active_sessions': len(self.focus_sessions),
                'last_session': self.focus_sessions[-1] if self.focus_sessions else None,
            }
        session = {
            'description': description,
            'minutes': minutes,
            'state': 'active',
            'started_at': time.time(),
        }
        self.focus_sessions.append(session)
        self._record_trace('focus_mode', {'description': description, 'minutes': minutes})
        return {
            'status': 'ok',
            'message': f'Focus mode started for {minutes} minutes',
            'session': session,
        }

    def manage_working_memory(self, params):
        action = (params.get('action') or '').lower() or 'store'
        key = params.get('key') or params.get('name') or params.get('arg0')
        value = params.get('value') if 'value' in params else params.get('arg1')
        if action in ('store', 'remember'):
            if key is None:
                return {'status': 'error', 'message': 'working_memory: key is required for store'}
            self.working_memory[str(key)] = value
            return {'status': 'ok', 'stored': True, 'key': key, 'value': value}
        if action in ('recall', 'get'):
            if key is None:
                return {'status': 'error', 'message': 'working_memory: key is required for recall'}
            return {'status': 'ok', 'key': key, 'value': self.working_memory.get(str(key))}
        if action in ('clear',):
            self.working_memory.clear()
            self._record_trace('working_memory', {'action': 'clear'})
            return {'status': 'ok', 'cleared': True}
        status = {
            'status': 'ok',
            'size': len(self.working_memory),
            'keys': list(self.working_memory.keys())[:20],
        }
        self._record_trace('working_memory', status)
        return status

    def record_intent(self, params):
        intent = {
            'goal': params.get('goal') or params.get('arg0'),
            'constraints': params.get('constraints'),
            'success': params.get('success') or params.get('definition_of_done'),
            'tags': params.get('tags'),
        }
        intent['meta'] = params
        self.intent_stack.append(intent)
        self._record_trace('intent', intent)
        return {'status': 'ok', 'intent': intent, 'stack_depth': len(self.intent_stack)}

    def record_decision(self, params):
        decision = {
            'label': params.get('label') or params.get('arg0'),
            'rationale': params.get('rationale') or params.get('why') or params.get('arg1'),
            'option': params.get('option'),
            'timestamp': time.time(),
        }
        self.decision_log.append(decision)
        self._record_trace('decision', decision)
        return {'status': 'ok', 'decision': decision, 'count': len(self.decision_log)}

    def toggle_trace(self, params):
        if 'enabled' in params:
            enabled = bool(params['enabled'])
        elif 'arg0' in params:
            enabled = str(params['arg0']).lower() in ('1', 'true', 'on', 'yes')
        else:
            enabled = True
        self.trace_enabled = enabled
        return {'status': 'ok', 'trace_enabled': self.trace_enabled}

    def explain_step(self, params):
        summary = {
            'profile': self.profile,
            'intents': self.intent_stack[-3:],
            'decisions': self.decision_log[-5:],
            'last_analysis': self.last_analysis,
            'lint_warnings': self.lint_warnings[-3:],
            'current_scope': self.scope_stack[-1] if self.scope_stack else None,
            'trace_tail': self.trace_log[-10:] if self.trace_enabled else [],
        }
        self._record_trace('explain_step', {'requested': True})
        return summary

    def set_profile(self, params):
        profile = params.get('profile') or params.get('arg0') or params.get('name')
        if profile is None:
            return {'status': 'error', 'message': 'profile name is required'}
        self.profile = str(profile).lower()
        self._record_trace('profile', {'profile': self.profile})
        return {'status': 'ok', 'profile': self.profile}

    def push_scope(self, name, meta, complexity=None):
        meta = meta or {}
        scope = {
            'name': name or f'scope_{len(self.scope_stack)}',
            'meta': meta,
        }
        warning = self._check_scope_budget(meta, complexity)
        if warning:
            scope['budget_warning'] = warning
            self.lint_warnings.append({'warnings': [warning], 'warning_count': 1})
        self.scope_stack.append(scope)
        self._record_trace('scope_enter', scope)
        return scope

    def pop_scope(self):
        if not self.scope_stack:
            return None
        scope = self.scope_stack.pop()
        self._record_trace('scope_exit', scope)
        return scope

    def _check_scope_budget(self, meta, complexity):
        budget = meta.get('budget') or meta.get('max_complexity') or meta.get('max_statements')
        if budget is None or complexity is None:
            return ''
        try:
            budget_val = int(budget)
        except Exception:
            return ''
        if complexity <= budget_val:
            return ''
        return f'Scope complexity {complexity} exceeds budget {budget_val}'

class _SonaCognitiveScope:
    def __init__(self, runtime, name, meta, complexity):
        self.runtime = runtime
        self.name = name
        self.meta = meta or {}
        self.complexity = complexity
    def __enter__(self):
        self.runtime.push_scope(self.name, self.meta, self.complexity)
        return self
    def __exit__(self, exc_type, exc, tb):
        self.runtime.pop_scope()
        return False

_sona_cognitive_runtime = _SonaCognitiveRuntime()

def sona_cognitive_check(**params):
    return _sona_cognitive_runtime.check_cognitive_load(params)

def sona_focus_mode(**params):
    return _sona_cognitive_runtime.configure_focus_mode(params)

def sona_working_memory(**params):
    return _sona_cognitive_runtime.manage_working_memory(params)

def sona_intent(**params):
    return _sona_cognitive_runtime.record_intent(params)

def sona_decision(**params):
    return _sona_cognitive_runtime.record_decision(params)

def sona_cognitive_trace(**params):
    return _sona_cognitive_runtime.toggle_trace(params)

def sona_explain_step(**params):
    return _sona_cognitive_runtime.explain_step(params)

def sona_profile(**params):
    return _sona_cognitive_runtime.set_profile(params)

def sona_cognitive_scope(name, meta=None, complexity=None):
    return _SonaCognitiveScope(_sona_cognitive_runtime, name, meta, complexity)
def sona_add(left, right):
    if isinstance(left, str) or isinstance(right, str):
        return str(left) + str(right)
    return left + right

sona_profile(arg0=[PositionalArgument(value=LiteralExpression(value='adhd', line_number=None))])
sona_intent(arg0=[KeywordArgument(name='goal', value=LiteralExpression(value='Summarize a short task list', line_number=None)), KeywordArgument(name='constraints', value=LiteralExpression(value='Keep output brief and clear', line_number=None)), KeywordArgument(name='success', value=LiteralExpression(value='Print prioritized list', line_number=None))])
sona_decision(arg0=[KeywordArgument(name='label', value=LiteralExpression(value='Ordering strategy', line_number=None)), KeywordArgument(name='rationale', value=LiteralExpression(value='Manual ordering keeps the summary predictable', line_number=None)), KeywordArgument(name='option', value=LiteralExpression(value='fixed-list', line_number=None))])
sona_cognitive_trace(arg0=[KeywordArgument(name='enabled', value=LiteralExpression(value=True, line_number=1))])
with sona_cognitive_scope('task-summary', {'arg0': 'task-summary', 'budget': 8}, complexity=6):
    tasks = ['Pay bills', 'Email team', 'Write summary']
    print('Task summary:')
    for task in tasks:
        print(sona_add('- ', task))
    sona_cognitive_check(arg0=[KeywordArgument(name='task', value=LiteralExpression(value='Summarize tasks', line_number=None)), KeywordArgument(name='context', value=LiteralExpression(value='Short list output for clarity', line_number=None))])
    sona_explain_step(arg0=None)
