use std::collections::HashMap;
use std::fmt;
use std::io::{self, Write};
use std::path::{Component, Path, PathBuf};
use std::time::Instant;

use hmac::{Hmac, Mac};
use sha2::{Digest, Sha256};
use sona_bytecode::{BytecodeProgram, Constant, FunctionBytecode, Instruction};
use sona_diagnostics::{Diagnostic, DiagnosticList, SonaResult, SourceSpan};
use sona_modules::{default_module_roots, ModuleResolver};
use sona_runtime::RuntimeConfig;

mod host;

type HmacSha256 = Hmac<Sha256>;

/// Redacted effect evidence emitted only when the caller enables Native Proof
/// observation.  Raw paths and argument values never leave the VM.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct NativeProofEffect {
    pub sequence: u64,
    pub scope: String,
    pub operation: String,
    pub outcome: String,
    pub target: Option<String>,
}

/// Incremental process-output and host-effect evidence for one native run.
/// It observes the existing runtime boundaries; it does not influence VM
/// evaluation or capability decisions.
#[derive(Clone, Debug)]
pub struct NativeProofEvidence {
    target_key: Vec<u8>,
    stdout: Sha256,
    stderr: Sha256,
    stdout_bytes: u64,
    stderr_bytes: u64,
    effects: Vec<NativeProofEffect>,
}

impl NativeProofEvidence {
    pub fn new(target_key: Vec<u8>) -> Self {
        Self {
            target_key,
            stdout: Sha256::new(),
            stderr: Sha256::new(),
            stdout_bytes: 0,
            stderr_bytes: 0,
            effects: Vec::new(),
        }
    }

    pub fn record_stdout(&mut self, bytes: &[u8]) {
        self.stdout.update(bytes);
        self.stdout_bytes = self.stdout_bytes.saturating_add(bytes.len() as u64);
    }

    pub fn record_stderr(&mut self, bytes: &[u8]) {
        self.stderr.update(bytes);
        self.stderr_bytes = self.stderr_bytes.saturating_add(bytes.len() as u64);
    }

    pub fn stdout_bytes(&self) -> u64 {
        self.stdout_bytes
    }

    pub fn stderr_bytes(&self) -> u64 {
        self.stderr_bytes
    }

    pub fn stdout_sha256(&self) -> String {
        sha256_label(self.stdout.clone().finalize().as_slice())
    }

    pub fn stderr_sha256(&self) -> String {
        sha256_label(self.stderr.clone().finalize().as_slice())
    }

    pub fn effects(&self) -> &[NativeProofEffect] {
        &self.effects
    }

    fn record_effect(
        &mut self,
        scope: &str,
        operation: &str,
        outcome: &str,
        target_identity: Option<String>,
    ) {
        let target = target_identity.map(|identity| {
            let mut mac = HmacSha256::new_from_slice(&self.target_key)
                .expect("HMAC accepts a non-empty SHA-256 key");
            mac.update(identity.as_bytes());
            format!("hmac-sha256:{}", hex_lower(&mac.finalize().into_bytes()))
        });
        self.effects.push(NativeProofEffect {
            sequence: (self.effects.len() as u64) + 1,
            scope: scope.to_string(),
            operation: operation.to_string(),
            outcome: outcome.to_string(),
            target,
        });
    }
}

fn hex_lower(bytes: &[u8]) -> String {
    bytes.iter().map(|byte| format!("{byte:02x}")).collect()
}

fn sha256_label(bytes: &[u8]) -> String {
    format!("sha256:{}", hex_lower(bytes))
}

fn lexical_normalize_path(path: &Path) -> PathBuf {
    let mut normalized = PathBuf::new();
    for component in path.components() {
        match component {
            Component::CurDir => {}
            Component::ParentDir => {
                let _ = normalized.pop();
            }
            Component::Prefix(prefix) => normalized.push(prefix.as_os_str()),
            Component::RootDir => normalized.push(component.as_os_str()),
            Component::Normal(part) => normalized.push(part),
        }
    }
    normalized
}

#[derive(Clone, Debug)]
pub enum Value {
    Null,
    Bool(bool),
    Int(i64),
    Float(f64),
    String(String),
    List(Vec<Value>),
    Map(HashMap<String, Value>),
    Function(FunctionBytecode),
    NativeFunction(&'static str),
    Module {
        name: String,
        exports: HashMap<String, Value>,
    },
}

impl Value {
    fn truthy(&self) -> bool {
        match self {
            Value::Null => false,
            Value::Bool(value) => *value,
            Value::Int(value) => *value != 0,
            Value::Float(value) => *value != 0.0,
            Value::String(value) => !value.is_empty(),
            Value::List(value) => !value.is_empty(),
            Value::Map(value) => !value.is_empty(),
            Value::Function(_) | Value::NativeFunction(_) | Value::Module { .. } => true,
        }
    }
}

impl fmt::Display for Value {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Value::Null => write!(f, "nil"),
            Value::Bool(value) => write!(f, "{value}"),
            Value::Int(value) => write!(f, "{value}"),
            Value::Float(value) => write!(f, "{value}"),
            Value::String(value) => write!(f, "{value}"),
            Value::List(items) => {
                write!(f, "[")?;
                for (index, item) in items.iter().enumerate() {
                    if index > 0 {
                        write!(f, ", ")?;
                    }
                    write!(f, "{item}")?;
                }
                write!(f, "]")
            }
            Value::Map(items) => {
                write!(f, "{{")?;
                let mut first = true;
                for (key, value) in items {
                    if !first {
                        write!(f, ", ")?;
                    }
                    first = false;
                    write!(f, "{key}: {value}")?;
                }
                write!(f, "}}")
            }
            Value::Function(function) => write!(f, "<func '{}'>", function.name),
            Value::NativeFunction(name) => write!(f, "<native-func '{name}'>"),
            Value::Module { name, .. } => write!(f, "<module '{name}'>"),
        }
    }
}

#[derive(Clone, Debug)]
struct Binding {
    value: Value,
    is_const: bool,
}

pub struct Vm {
    pub config: RuntimeConfig,
    globals: HashMap<String, Binding>,
    frames: Vec<HashMap<String, Binding>>,
    stack: Vec<Value>,
    output: Vec<String>,
    instruction_count: usize,
    call_depth: usize,
    resolver: ModuleResolver,
    random_state: u64,
    started_at: Instant,
    proof: Option<NativeProofEvidence>,
}

impl Vm {
    pub fn new(entry_path: Option<PathBuf>) -> Self {
        let roots = entry_path
            .as_ref()
            .map(default_module_roots)
            .unwrap_or_default();
        Self::with_resolver(ModuleResolver::new(roots))
    }

    pub fn with_resolver(resolver: ModuleResolver) -> Self {
        let mut globals = HashMap::new();
        globals.insert(
            "print".to_string(),
            Binding {
                value: Value::NativeFunction("print"),
                is_const: true,
            },
        );
        Self {
            config: RuntimeConfig::default(),
            globals,
            frames: Vec::new(),
            stack: Vec::new(),
            output: Vec::new(),
            instruction_count: 0,
            call_depth: 0,
            resolver,
            random_state: 0x534f_4e41_0154,
            started_at: Instant::now(),
            proof: None,
        }
    }

    pub fn output(&self) -> &[String] {
        &self.output
    }

    /// Enable redacted Proof Mode observation for this VM instance.  This is
    /// deliberately opt-in so ordinary native runs retain no proof state.
    pub fn enable_proof_observation(&mut self, target_key: Vec<u8>) {
        self.proof = Some(NativeProofEvidence::new(target_key));
    }

    /// Return the collected evidence after execution.  The caller may append
    /// CLI-rendered diagnostics to the output digests before serializing a
    /// receipt.
    pub fn take_proof_evidence(&mut self) -> Option<NativeProofEvidence> {
        self.proof.take()
    }

    pub(crate) fn emit_stdout(&mut self, text: &str) -> io::Result<()> {
        {
            let stdout = io::stdout();
            let mut output = stdout.lock();
            output.write_all(text.as_bytes())?;
            output.flush()?;
        }
        if let Some(proof) = self.proof.as_mut() {
            proof.record_stdout(text.as_bytes());
        }
        Ok(())
    }

    pub(crate) fn emit_stderr(&mut self, text: &str) -> io::Result<()> {
        {
            let stderr = io::stderr();
            let mut output = stderr.lock();
            output.write_all(text.as_bytes())?;
            output.flush()?;
        }
        if let Some(proof) = self.proof.as_mut() {
            proof.record_stderr(text.as_bytes());
        }
        Ok(())
    }

    pub(crate) fn record_proof_effect(
        &mut self,
        scope: &str,
        operation: &str,
        outcome: &str,
        target_identity: Option<String>,
    ) {
        if let Some(proof) = self.proof.as_mut() {
            proof.record_effect(scope, operation, outcome, target_identity);
        }
    }

    pub(crate) fn proof_filesystem_target(&self, value: Option<&Value>) -> Option<String> {
        let Value::String(raw) = value? else {
            return None;
        };
        let path = Path::new(raw);
        let absolute = if path.is_absolute() {
            path.to_path_buf()
        } else {
            std::env::current_dir().ok()?.join(path)
        };
        let identity =
            std::fs::canonicalize(&absolute).unwrap_or_else(|_| lexical_normalize_path(&absolute));
        Some(format!(
            "filesystem\u{0}{}",
            identity.to_string_lossy().replace('\\', "/")
        ))
    }

    pub fn execute(&mut self, program: &BytecodeProgram) -> SonaResult<Value> {
        self.execute_instructions(&program.instructions)
    }

    fn execute_instructions(&mut self, instructions: &[Instruction]) -> SonaResult<Value> {
        let mut ip = 0usize;
        while ip < instructions.len() {
            self.tick()?;
            match &instructions[ip] {
                Instruction::LoadConst(value) => self.stack.push(value_from_constant(value)),
                Instruction::LoadName(name) => self.stack.push(self.load_name(name)?),
                Instruction::DeclareName { name, is_const } => {
                    let value = self.pop_stack()?;
                    self.current_scope().insert(
                        name.clone(),
                        Binding {
                            value,
                            is_const: *is_const,
                        },
                    );
                }
                Instruction::StoreName(name) => {
                    let value = self.pop_stack()?;
                    self.store_name(name, value)?;
                }
                Instruction::DefineFunction(function) => {
                    self.current_scope().insert(
                        function.name.clone(),
                        Binding {
                            value: Value::Function(function.clone()),
                            is_const: true,
                        },
                    );
                }
                Instruction::Pop => {
                    self.stack.pop();
                }
                Instruction::Return => return Ok(self.stack.pop().unwrap_or(Value::Null)),
                Instruction::Jump(target) => {
                    ip = *target;
                    continue;
                }
                Instruction::JumpIfFalse(target) => {
                    let value = self.pop_stack()?;
                    if !value.truthy() {
                        ip = *target;
                        continue;
                    }
                }
                Instruction::Import(name) => self.import_module(name)?,
                Instruction::GetMember(name) => {
                    let object = self.pop_stack()?;
                    self.stack.push(self.get_member(object, name)?);
                }
                Instruction::BuildList(count) => {
                    let mut items = Vec::new();
                    for _ in 0..*count {
                        items.push(self.pop_stack()?);
                    }
                    items.reverse();
                    self.stack.push(Value::List(items));
                }
                Instruction::BuildMap(keys) => {
                    let mut map = HashMap::new();
                    for key in keys.iter().rev() {
                        map.insert(key.clone(), self.pop_stack()?);
                    }
                    self.stack.push(Value::Map(map));
                }
                Instruction::Call(argc) => self.call(*argc)?,
                Instruction::Add => self.binary_add()?,
                Instruction::Subtract => self.numeric_binary("subtract", |a, b| a - b)?,
                Instruction::Multiply => self.numeric_binary("multiply", |a, b| a * b)?,
                Instruction::Divide => self.divide(false)?,
                Instruction::Modulo => self.divide(true)?,
                Instruction::Power => self.numeric_binary("power", |a, b| a.powf(b))?,
                Instruction::Negate => self.negate()?,
                Instruction::Not => {
                    let value = self.pop_stack()?;
                    self.stack.push(Value::Bool(!value.truthy()));
                }
                Instruction::Equal => self.compare_eq(false)?,
                Instruction::NotEqual => self.compare_eq(true)?,
                Instruction::Less => self.compare_order("<", |a, b| a < b)?,
                Instruction::LessEqual => self.compare_order("<=", |a, b| a <= b)?,
                Instruction::Greater => self.compare_order(">", |a, b| a > b)?,
                Instruction::GreaterEqual => self.compare_order(">=", |a, b| a >= b)?,
            }
            ip += 1;
        }
        Ok(Value::Null)
    }

    fn tick(&mut self) -> SonaResult<()> {
        self.instruction_count += 1;
        if self.instruction_count > self.config.limits.max_instructions {
            return Err(DiagnosticList::single(Diagnostic::error(
                "E0306",
                "SONA-NATIVE-RUNTIME-010",
                "runtime",
                "Native instruction limit exceeded.",
                SourceSpan::unknown(),
                "Increase the limit or rewrite the loop.",
            )));
        }
        Ok(())
    }

    fn current_scope(&mut self) -> &mut HashMap<String, Binding> {
        self.frames.last_mut().unwrap_or(&mut self.globals)
    }

    fn load_name(&self, name: &str) -> SonaResult<Value> {
        for frame in self.frames.iter().rev() {
            if let Some(binding) = frame.get(name) {
                return Ok(binding.value.clone());
            }
        }
        self.globals
            .get(name)
            .map(|binding| binding.value.clone())
            .ok_or_else(|| {
                DiagnosticList::single(Diagnostic::error(
                    "E0401",
                    "SONA-NATIVE-RUNTIME-003",
                    "runtime",
                    format!("Name '{name}' is not defined."),
                    SourceSpan::unknown(),
                    "Declare the name before using it.",
                ))
            })
    }

    fn store_name(&mut self, name: &str, value: Value) -> SonaResult<()> {
        for frame in self.frames.iter_mut().rev() {
            if let Some(binding) = frame.get_mut(name) {
                if binding.is_const {
                    return Err(const_error(name));
                }
                binding.value = value;
                return Ok(());
            }
        }
        if let Some(binding) = self.globals.get_mut(name) {
            if binding.is_const {
                return Err(const_error(name));
            }
            binding.value = value;
            return Ok(());
        }
        self.current_scope().insert(
            name.to_string(),
            Binding {
                value,
                is_const: false,
            },
        );
        Ok(())
    }

    fn import_module(&mut self, name: &str) -> SonaResult<()> {
        if !self.resolver.contains(name) {
            if let Some(exports) = host::module_exports(name) {
                self.globals.insert(
                    name.to_string(),
                    Binding {
                        value: Value::Module {
                            name: name.to_string(),
                            exports,
                        },
                        is_const: true,
                    },
                );
                return Ok(());
            }
        }
        let record = self.resolver.load(name)?;
        let mut module_vm = Vm::with_resolver(self.resolver.clone());
        module_vm.config = self.config.clone();
        // Workspace modules execute in an isolated VM, but Proof Mode remains
        // one observer for the complete program. Move the observer through the
        // nested execution so output hashes and effect sequence stay exact.
        module_vm.proof = self.proof.take();
        let module_result = module_vm.execute(&record.bytecode);
        self.proof = module_vm.proof.take();
        module_result?;
        let mut exports = HashMap::new();
        for (key, binding) in module_vm.globals {
            if key != "print" {
                exports.insert(key, binding.value);
            }
        }
        self.globals.insert(
            name.to_string(),
            Binding {
                value: Value::Module {
                    name: name.to_string(),
                    exports,
                },
                is_const: true,
            },
        );
        Ok(())
    }

    fn get_member(&self, object: Value, name: &str) -> SonaResult<Value> {
        match object {
            Value::Module { exports, .. } => exports.get(name).cloned().ok_or_else(|| {
                DiagnosticList::single(Diagnostic::error(
                    "E0300",
                    "SONA-NATIVE-RUNTIME-007",
                    "runtime",
                    format!("Object has no method '{name}'."),
                    SourceSpan::unknown(),
                    "Call an exported module function.",
                ))
            }),
            Value::Map(map) => map.get(name).cloned().ok_or_else(|| {
                DiagnosticList::single(Diagnostic::error(
                    "E0302",
                    "SONA-NATIVE-RUNTIME-006",
                    "runtime",
                    format!("Map key '{name}' was not found."),
                    SourceSpan::unknown(),
                    "Use an existing map key.",
                ))
            }),
            _ => Err(DiagnosticList::single(Diagnostic::error(
                "E0200",
                "SONA-NATIVE-RUNTIME-005",
                "runtime",
                "Only modules and maps support member access in the native preview.",
                SourceSpan::unknown(),
                "Use a module/map value before '.'.",
            ))),
        }
    }

    fn call(&mut self, argc: usize) -> SonaResult<()> {
        let mut args = Vec::new();
        for _ in 0..argc {
            args.push(self.pop_stack()?);
        }
        args.reverse();
        let callee = self.pop_stack()?;
        match callee {
            Value::NativeFunction("print") => {
                if !self.config.capabilities.console {
                    let diagnostic = DiagnosticList::single(Diagnostic::error(
                        "E0300",
                        "SONA-NATIVE-POLICY-001",
                        "policy",
                        "Console output is disabled by runtime policy.",
                        SourceSpan::unknown(),
                        "Enable console capability for this run.",
                    ));
                    self.record_proof_effect("console", "print", "denied", None);
                    return Err(diagnostic);
                }
                let line = args.first().map(ToString::to_string).unwrap_or_default();
                let result = self.emit_stdout(&format!("{line}\n"));
                self.record_proof_effect(
                    "console",
                    "print",
                    if result.is_ok() { "allowed" } else { "failed" },
                    None,
                );
                result.map_err(console_output_error)?;
                self.output.push(line);
                self.stack.push(Value::Null);
            }
            Value::NativeFunction(name) => {
                let result = self.call_host(name, args)?;
                self.stack.push(result);
            }
            Value::Function(function) => {
                if self.call_depth >= self.config.limits.max_call_depth {
                    return Err(DiagnosticList::single(Diagnostic::error(
                        "E0305",
                        "SONA-NATIVE-RUNTIME-011",
                        "runtime",
                        "Native call depth limit exceeded.",
                        SourceSpan::unknown(),
                        "Reduce recursion depth or increase the limit.",
                    )));
                }
                let mut frame = HashMap::new();
                for (index, param) in function.params.iter().enumerate() {
                    let value = if let Some(arg) = args.get(index) {
                        arg.clone()
                    } else if let Some(Some(default_code)) = function.defaults.get(index) {
                        self.execute_instructions(default_code)?
                    } else {
                        return Err(DiagnosticList::single(Diagnostic::error(
                            "E0300",
                            "SONA-NATIVE-RUNTIME-001",
                            "runtime",
                            format!(
                                "Function '{}' missing required argument: {param}",
                                function.name
                            ),
                            SourceSpan::unknown(),
                            "Pass the required arguments.",
                        )));
                    };
                    frame.insert(
                        param.clone(),
                        Binding {
                            value,
                            is_const: false,
                        },
                    );
                }
                self.call_depth += 1;
                self.frames.push(frame);
                let result = self.execute_instructions(&function.body);
                self.frames.pop();
                self.call_depth -= 1;
                self.stack.push(result?);
            }
            _ => {
                return Err(DiagnosticList::single(Diagnostic::error(
                    "E0203",
                    "SONA-NATIVE-RUNTIME-002",
                    "runtime",
                    "Value is not callable.",
                    SourceSpan::unknown(),
                    "Call a function value.",
                )))
            }
        }
        Ok(())
    }

    fn pop_stack(&mut self) -> SonaResult<Value> {
        self.stack.pop().ok_or_else(|| {
            DiagnosticList::single(Diagnostic::error(
                "E0300",
                "SONA-NATIVE-RUNTIME-099",
                "runtime",
                "Native VM stack underflow.",
                SourceSpan::unknown(),
                "Report this internal native-runtime defect.",
            ))
        })
    }

    fn binary_add(&mut self) -> SonaResult<()> {
        let right = self.pop_stack()?;
        let left = self.pop_stack()?;
        self.stack.push(match (left, right) {
            (Value::String(a), b) => Value::String(format!("{a}{b}")),
            (a, Value::String(b)) => Value::String(format!("{a}{b}")),
            (Value::Int(a), Value::Int(b)) => Value::Int(a + b),
            (Value::Int(a), Value::Float(b)) => Value::Float(a as f64 + b),
            (Value::Float(a), Value::Int(b)) => Value::Float(a + b as f64),
            (Value::Float(a), Value::Float(b)) => Value::Float(a + b),
            (Value::Bool(a), Value::Int(b)) => Value::Int((a as i64) + b),
            (Value::Int(a), Value::Bool(b)) => Value::Int(a + (b as i64)),
            (Value::List(mut a), Value::List(b)) => {
                a.extend(b);
                Value::List(a)
            }
            _ => return Err(type_error("Unsupported operands for '+'.")),
        });
        Ok(())
    }

    fn numeric_binary(&mut self, message: &str, op: impl Fn(f64, f64) -> f64) -> SonaResult<()> {
        let right = self.pop_stack()?;
        let left = self.pop_stack()?;
        let a = number(&left)?;
        let b = number(&right)?;
        let result = op(a, b);
        self.stack.push(
            if matches!((left, right), (Value::Int(_), Value::Int(_))) && result.fract() == 0.0 {
                Value::Int(result as i64)
            } else {
                Value::Float(result)
            },
        );
        let _ = message;
        Ok(())
    }

    fn divide(&mut self, modulo: bool) -> SonaResult<()> {
        let right = self.pop_stack()?;
        let left = self.pop_stack()?;
        let b = number(&right)?;
        if b == 0.0 {
            return Err(DiagnosticList::single(Diagnostic::error(
                "E0301",
                "SONA-NATIVE-RUNTIME-004",
                "runtime",
                "Division or modulo by zero.",
                SourceSpan::unknown(),
                "Use a nonzero divisor.",
            )));
        }
        let a = number(&left)?;
        let result = if modulo { a % b } else { a / b };
        self.stack.push(
            if matches!((left, right), (Value::Int(_), Value::Int(_))) && result.fract() == 0.0 {
                Value::Int(result as i64)
            } else {
                Value::Float(result)
            },
        );
        Ok(())
    }

    fn negate(&mut self) -> SonaResult<()> {
        let value = self.pop_stack()?;
        self.stack.push(match value {
            Value::Int(value) => Value::Int(-value),
            Value::Float(value) => Value::Float(-value),
            _ => return Err(type_error("Unary '-' requires a number.")),
        });
        Ok(())
    }

    fn compare_eq(&mut self, negate: bool) -> SonaResult<()> {
        let right = self.pop_stack()?;
        let left = self.pop_stack()?;
        let eq = values_equal(&left, &right);
        self.stack.push(Value::Bool(if negate { !eq } else { eq }));
        Ok(())
    }

    fn compare_order(&mut self, _op_name: &str, op: impl Fn(f64, f64) -> bool) -> SonaResult<()> {
        let right = self.pop_stack()?;
        let left = self.pop_stack()?;
        self.stack
            .push(Value::Bool(op(number(&left)?, number(&right)?)));
        Ok(())
    }
}

fn value_from_constant(value: &Constant) -> Value {
    match value {
        Constant::Null => Value::Null,
        Constant::Bool(value) => Value::Bool(*value),
        Constant::Int(value) => Value::Int(*value),
        Constant::Float(value) => Value::Float(*value),
        Constant::String(value) => Value::String(value.clone()),
    }
}

fn number(value: &Value) -> SonaResult<f64> {
    match value {
        Value::Int(value) => Ok(*value as f64),
        Value::Float(value) => Ok(*value),
        Value::Bool(value) => Ok(if *value { 1.0 } else { 0.0 }),
        _ => Err(type_error("Numeric operation requires numbers.")),
    }
}

fn values_equal(left: &Value, right: &Value) -> bool {
    match (left, right) {
        (Value::Null, Value::Null) => true,
        (Value::Bool(a), Value::Bool(b)) => a == b,
        (Value::Int(a), Value::Int(b)) => a == b,
        (Value::Float(a), Value::Float(b)) => a == b,
        (Value::Int(a), Value::Float(b)) => (*a as f64) == *b,
        (Value::Float(a), Value::Int(b)) => *a == (*b as f64),
        (Value::String(a), Value::String(b)) => a == b,
        _ => false,
    }
}

fn type_error(message: impl Into<String>) -> DiagnosticList {
    DiagnosticList::single(Diagnostic::error(
        "E0200",
        "SONA-NATIVE-RUNTIME-005",
        "runtime",
        message,
        SourceSpan::unknown(),
        "Use operands supported by the Sona Native Core profile.",
    ))
}

fn console_output_error(_error: std::io::Error) -> DiagnosticList {
    DiagnosticList::single(Diagnostic::error(
        "E0600",
        "SONA-IO-002",
        "io",
        "Console output failed.",
        SourceSpan::unknown(),
        "Check the output destination and run the program again.",
    ))
}

fn const_error(name: &str) -> DiagnosticList {
    DiagnosticList::single(Diagnostic::error(
        "E0403",
        "SONA-NATIVE-RUNTIME-008",
        "runtime",
        format!("Cannot reassign const '{name}'."),
        SourceSpan::unknown(),
        "Use let for mutable values.",
    ))
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;
    use std::time::{SystemTime, UNIX_EPOCH};

    use sona_bytecode::compile;
    use sona_ir::lower;
    use sona_parser::parse_source;
    use sona_source::SourceFile;

    #[test]
    fn runs_arithmetic_and_functions() {
        let source = SourceFile::new(
            0,
            "test.sona",
            "func add(a,b){ return a+b; }; print(add(2,3));",
        );
        let ast = parse_source(&source).unwrap();
        let bytecode = compile(lower(ast).unwrap(), Some(source.text)).unwrap();
        let mut vm = Vm::new(None);
        vm.execute(&bytecode).unwrap();
        assert_eq!(vm.output(), &["5".to_string()]);
    }

    #[test]
    fn evaluates_default_parameters_before_entering_the_function_frame() {
        let source = SourceFile::new(
            0,
            "test.sona",
            "func add(left, right=4) { return left + right; }; print(add(6));",
        );
        let ast = parse_source(&source).unwrap();
        let bytecode = compile(lower(ast).unwrap(), Some(source.text)).unwrap();
        let mut vm = Vm::new(None);
        vm.execute(&bytecode).unwrap();
        assert_eq!(vm.output(), &["10"]);
    }

    fn compile_source(name: &str, text: &str) -> BytecodeProgram {
        let source = SourceFile::new(0, name, text);
        let ast = parse_source(&source).unwrap();
        compile(lower(ast).unwrap(), Some(source.text)).unwrap()
    }

    fn temporary_directory(label: &str) -> PathBuf {
        let nonce = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_nanos();
        let path = std::env::temp_dir().join(format!("sona-0154-{label}-{nonce}"));
        fs::create_dir_all(&path).unwrap();
        path
    }

    #[test]
    fn runs_foundation_host_modules_without_workspace_wrappers() {
        let bytecode = compile_source(
            "foundation.sona",
            r#"
                import string;
                import math;
                import json;
                import collection;
                print(string.upper("sona"));
                print(math.sqrt(81));
                print(json.stringify(json.parse("{\"b\":2,\"a\":1}")));
                print(collection.first([4, 5, 6]));
            "#,
        );
        let mut vm = Vm::new(None);
        vm.execute(&bytecode).unwrap();
        assert_eq!(vm.output(), &["SONA", "9", "{\"a\": 1, \"b\": 2}", "4"]);
    }

    #[test]
    fn native_filesystem_is_default_denied_then_explicitly_granted() {
        let root = temporary_directory("fs");
        let target = root.join("snow-\u{2603}.txt");
        let path = target.to_string_lossy().replace('\\', "/");
        let source = format!(
            "import fs; fs.write_text(\"{path}\", \"Sona\"); print(fs.read_text(\"{path}\"));"
        );
        let bytecode = compile_source("fs.sona", &source);

        let mut denied = Vm::new(None);
        let error = denied.execute(&bytecode).unwrap_err();
        assert_eq!(error.0[0].diagnostic_id, "SONA-FS-005");

        let mut allowed = Vm::new(None);
        allowed.config.capabilities.filesystem_read = true;
        allowed.config.capabilities.filesystem_write = true;
        allowed.execute(&bytecode).unwrap();
        assert_eq!(allowed.output(), &["Sona"]);
        assert_eq!(fs::read_to_string(&target).unwrap(), "Sona");
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn workspace_module_precedes_host_registry() {
        let root = temporary_directory("precedence");
        fs::write(
            root.join("string.smod"),
            "func upper(value) { return \"workspace\"; };",
        )
        .unwrap();
        let entry = root.join("app.sona");
        let bytecode = compile_source(
            entry.to_string_lossy().as_ref(),
            "import string; print(string.upper(\"sona\"));",
        );
        let mut vm = Vm::new(Some(entry));
        vm.execute(&bytecode).unwrap();
        assert_eq!(vm.output(), &["workspace"]);
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn proof_observation_includes_workspace_module_output_and_effects() {
        let root = temporary_directory("proof-module");
        let target = root.join("target.txt");
        fs::write(&target, "present").unwrap();
        let normalized_target = target.to_string_lossy().replace('\\', "/");
        fs::write(
            root.join("helper.smod"),
            format!("import fs; fs.exists(\"{normalized_target}\"); print(\"module\");"),
        )
        .unwrap();
        let entry = root.join("app.sona");
        let bytecode = compile_source(
            entry.to_string_lossy().as_ref(),
            "import helper; print(\"main\");",
        );
        let mut vm = Vm::new(Some(entry));
        vm.config.capabilities.filesystem_read = true;
        vm.enable_proof_observation(vec![7; 32]);
        vm.execute(&bytecode).unwrap();
        let evidence = vm.take_proof_evidence().unwrap();
        assert_eq!(
            evidence.stdout_sha256(),
            sha256_label(Sha256::digest(b"module\nmain\n").as_slice())
        );
        assert_eq!(evidence.stdout_bytes(), 12);
        assert_eq!(evidence.effects().len(), 3);
        assert_eq!(evidence.effects()[0].scope, "filesystem");
        assert_eq!(evidence.effects()[1].operation, "print");
        assert_eq!(evidence.effects()[2].operation, "print");
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn proof_hashes_match_fixed_sha256_and_hmac_vectors() {
        let mut evidence = NativeProofEvidence::new(vec![0x0b; 20]);
        evidence.record_stdout(b"abc");
        evidence.record_effect(
            "filesystem",
            "read",
            "allowed",
            Some("Hi There".to_string()),
        );

        assert_eq!(
            evidence.stdout_sha256(),
            "sha256:ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
        );
        assert_eq!(
            evidence.effects()[0].target.as_deref(),
            Some("hmac-sha256:b0344c61d8db38535ca8afceaf0bf12b881dc200c9833da726e9376c2e32cff7")
        );
    }

    #[test]
    fn native_http_is_importable_but_reports_stable_unavailable_diagnostic() {
        let bytecode = compile_source(
            "http.sona",
            "import http; http.get(\"https://example.invalid/private?token=secret\");",
        );
        let mut vm = Vm::new(None);
        vm.config.capabilities.network = true;
        let error = vm.execute(&bytecode).unwrap_err();
        assert_eq!(error.0[0].diagnostic_id, "SONA-HTTP-005");
        assert!(!error.0[0].message.contains("secret"));
    }

    #[test]
    fn seeded_native_random_is_repeatable() {
        let bytecode = compile_source(
            "random.sona",
            "import random; random.seed(42); print(random.integer(1, 100)); random.seed(42); print(random.integer(1, 100));",
        );
        let mut vm = Vm::new(None);
        vm.execute(&bytecode).unwrap();
        assert_eq!(vm.output().len(), 2);
        assert_eq!(vm.output()[0], vm.output()[1]);
    }
}
