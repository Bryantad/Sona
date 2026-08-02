use std::collections::HashMap;
use std::path::{Path, PathBuf};

use sona_bytecode::{compile, BytecodeProgram};
use sona_diagnostics::{Diagnostic, DiagnosticList, SonaResult, SourceSpan};
use sona_ir::lower;
use sona_parser::parse_source;
use sona_source::SourceFile;

#[derive(Clone, Debug)]
pub struct ModuleRecord {
    pub name: String,
    pub path: PathBuf,
    pub bytecode: BytecodeProgram,
}

#[derive(Clone, Debug)]
pub struct ModuleResolver {
    roots: Vec<PathBuf>,
    loaded: HashMap<String, ModuleRecord>,
    in_progress: Vec<String>,
}

impl ModuleResolver {
    pub fn new(roots: Vec<PathBuf>) -> Self {
        Self {
            roots,
            loaded: HashMap::new(),
            in_progress: Vec::new(),
        }
    }

    pub fn roots(&self) -> &[PathBuf] {
        &self.roots
    }

    /// Return true when a workspace/module-root implementation exists.
    ///
    /// The VM uses this before consulting its built-in host registry so an
    /// application-provided ``.smod`` keeps the established precedence.
    pub fn contains(&self, name: &str) -> bool {
        let relative = name.replace('.', "/") + ".smod";
        self.roots
            .iter()
            .map(|root| root.join(&relative))
            .any(|candidate| candidate.is_file())
    }

    pub fn load(&mut self, name: &str) -> SonaResult<ModuleRecord> {
        if let Some(record) = self.loaded.get(name) {
            return Ok(record.clone());
        }
        if self.in_progress.iter().any(|item| item == name) {
            return Err(DiagnosticList::single(Diagnostic::error(
                "E0102",
                "SONA-NATIVE-MODULE-002",
                "module",
                format!("Circular import while loading '{name}'."),
                SourceSpan::unknown(),
                "Break the module cycle or move shared code into a third module.",
            )));
        }
        let path = self.resolve(name)?;
        self.in_progress.push(name.to_string());
        let source = SourceFile::read(0, &path).map_err(|err| {
            DiagnosticList::single(Diagnostic::error(
                "E0105",
                "SONA-NATIVE-MODULE-003",
                "module",
                format!("Could not read module '{name}': {err}"),
                SourceSpan::new(path.display().to_string(), 1, 1, 1, 1),
                "Check file permissions and module path.",
            ))
        })?;
        let ast = parse_source(&source)?;
        let ir = lower(ast)?;
        let bytecode = compile(ir, Some(source.text.clone()))?;
        let record = ModuleRecord {
            name: name.to_string(),
            path,
            bytecode,
        };
        self.loaded.insert(name.to_string(), record.clone());
        self.in_progress.pop();
        Ok(record)
    }

    fn resolve(&self, name: &str) -> SonaResult<PathBuf> {
        let relative = name.replace('.', "/") + ".smod";
        for root in &self.roots {
            let candidate = root.join(&relative);
            if candidate.exists() && candidate.is_file() {
                return Ok(candidate);
            }
        }
        Err(DiagnosticList::single(Diagnostic::error(
            "E0100",
            "SONA-NATIVE-MODULE-001",
            "module",
            format!("Module '{name}' was not found."),
            SourceSpan::new("<import>", 1, 1, 1, 1),
            "Add a .smod file under a native module root.",
        )))
    }
}

pub fn default_module_roots(entry: impl AsRef<Path>) -> Vec<PathBuf> {
    let entry = entry.as_ref();
    let mut roots = Vec::new();
    if let Some(parent) = entry.parent() {
        roots.push(parent.to_path_buf());
        roots.push(parent.join("modules"));
    }
    roots
}
