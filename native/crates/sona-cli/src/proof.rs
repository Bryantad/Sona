//! Native Proof Mode command and receipt persistence.
//!
//! `PROOF-XXX` is reserved for this command, its receipt contract, and its
//! persistence boundary.  Program parsing, container loading, VM execution,
//! engine selection, and capability failures intentionally retain their
//! existing stable Sona diagnostic identifiers.

use std::fs::{self, File, OpenOptions};
use std::io::{self, Write};
use std::path::{Path, PathBuf};
use std::time::Instant;

use chrono::{SecondsFormat, Utc};
use serde_json::{json, Map, Value};
use sha2::{Digest, Sha256};
use sona_bytecode::{compile, decode_source_backed_payload};
use sona_diagnostics::{Diagnostic, DiagnosticList, SonaResult, SourceSpan};
use sona_ir::lower;
use sona_parser::parse_source;
use sona_runtime::RuntimeCapabilities;
use sona_source::SourceFile;
use sona_vm::{NativeProofEffect, NativeProofEvidence, Vm};

const SCHEMA_ID: &str = "sona.native-proof.schema-1";

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum PersistenceFault {
    Creation,
    Serialization,
    Finalization,
}

#[cfg_attr(windows, allow(dead_code))]
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum PublicationState {
    NotPublished,
    Published,
}

#[derive(Clone, Debug)]
struct ProofContext {
    timestamp_utc: String,
    target_key: Vec<u8>,
    forced_duration_ms: Option<u64>,
    fault: Option<PersistenceFault>,
}

impl ProofContext {
    fn production() -> SonaResult<Self> {
        let mut target_key = vec![0u8; 32];
        getrandom::getrandom(&mut target_key).map_err(|_| {
            proof_error(
                "PROOF-005",
                "E0600",
                "Receipt creation failed.",
                "Try the proof again with a writable receipt destination.",
            )
        })?;
        Ok(Self {
            timestamp_utc: Utc::now().to_rfc3339_opts(SecondsFormat::Secs, true),
            target_key,
            forced_duration_ms: None,
            fault: None,
        })
    }
}

#[derive(Clone, Debug)]
struct ProgramIdentity {
    kind: &'static str,
    container: Option<(String, u64)>,
    source_sha256: String,
    source_bytes: u64,
}

#[derive(Debug)]
struct PreparedProgram {
    source: SourceFile,
    entry_path: PathBuf,
    identity: ProgramIdentity,
}

/// Run Proof Mode.  The command returns an existing program diagnostic when
/// execution fails after its receipt was safely written; Proof-only failures
/// use the compact `PROOF-XXX` namespace.
pub(super) fn run(args: &[String], version: &str) -> SonaResult<i32> {
    run_with_context(args, version, None)
}

fn run_with_context(
    args: &[String],
    version: &str,
    supplied_context: Option<ProofContext>,
) -> SonaResult<i32> {
    let (target, receipt_path) = parse_invocation(args)?;
    super::require_native_engine(args)?;
    validate_receipt_destination(&receipt_path)?;

    // A container must validate its exact source backing before it is eligible
    // for a Proof receipt.  Existing bytecode diagnostics retain ownership.
    let prepared = prepare_program(&target)?;
    let context = supplied_context.unwrap_or(ProofContext::production()?);
    let identity = prepared.identity.clone();
    let capabilities = super::runtime_capabilities(args);
    let started = Instant::now();
    let (mut evidence, program_error) =
        execute_prepared(prepared, capabilities.clone(), &context.target_key);
    let duration_ms = context
        .forced_duration_ms
        .unwrap_or_else(|| started.elapsed().as_millis().min(u128::from(u64::MAX)) as u64);

    // Native CLI diagnostics are emitted after `run` returns.  Hash the exact
    // rendered bytes now so the persisted receipt describes the process output
    // without buffering or replaying program output from the VM.
    if let Some(diagnostics) = program_error.as_ref() {
        evidence.record_stderr(format!("{diagnostics}\n").as_bytes());
    }

    let receipt = build_receipt_for_program(
        version,
        &identity,
        capabilities,
        duration_ms,
        &evidence,
        program_error.as_ref(),
        &context,
    )?;
    persist_receipt(&receipt_path, &receipt, context.fault)?;

    if let Some(diagnostics) = program_error {
        return Err(diagnostics);
    }
    Ok(0)
}

fn parse_invocation(args: &[String]) -> SonaResult<(PathBuf, PathBuf)> {
    let Some(target) = args.get(1) else {
        return Err(proof_error(
            "PROOF-001",
            "E0001",
            "Invalid Proof Mode invocation.",
            "Use 'sona proof <program.sona|program.sbc> --receipt <path>'.",
        ));
    };
    if target.starts_with('-') {
        return Err(proof_error(
            "PROOF-001",
            "E0001",
            "Invalid Proof Mode invocation.",
            "Provide a .sona or .sbc program before Proof Mode options.",
        ));
    }
    let positions = args
        .iter()
        .enumerate()
        .filter_map(|(index, item)| (item == "--receipt").then_some(index))
        .collect::<Vec<_>>();
    if positions.len() != 1 {
        return Err(proof_error(
            "PROOF-001",
            "E0001",
            "Invalid Proof Mode invocation.",
            "Provide exactly one --receipt <path> option.",
        ));
    }
    let receipt_index = positions[0];
    let Some(receipt) = args.get(receipt_index + 1) else {
        return Err(proof_error(
            "PROOF-001",
            "E0001",
            "Invalid Proof Mode invocation.",
            "Provide a path after --receipt.",
        ));
    };
    if receipt.is_empty() || receipt.starts_with('-') {
        return Err(proof_error(
            "PROOF-001",
            "E0001",
            "Invalid Proof Mode invocation.",
            "Provide a non-option path after --receipt.",
        ));
    }
    Ok((PathBuf::from(target), PathBuf::from(receipt)))
}

fn validate_receipt_destination(destination: &Path) -> SonaResult<()> {
    let parent = destination
        .parent()
        .filter(|path| !path.as_os_str().is_empty())
        .unwrap_or_else(|| Path::new("."));
    match fs::metadata(parent) {
        Ok(metadata) if metadata.is_dir() => {}
        _ => {
            return Err(proof_error(
                "PROOF-003",
                "E0601",
                "Invalid receipt destination.",
                "Create the receipt parent directory and provide a new file path.",
            ))
        }
    }
    match fs::symlink_metadata(destination) {
        Ok(metadata) if metadata.file_type().is_dir() => Err(proof_error(
            "PROOF-003",
            "E0601",
            "Invalid receipt destination.",
            "Provide a new receipt file path, not a directory.",
        )),
        Ok(_) => Err(proof_error(
            "PROOF-004",
            "E0601",
            "Receipt destination already exists.",
            "Provide a new, unused receipt path.",
        )),
        Err(error) if error.kind() == io::ErrorKind::NotFound => Ok(()),
        Err(_) => Err(proof_error(
            "PROOF-003",
            "E0601",
            "Invalid receipt destination.",
            "Provide a receipt path whose parent can be inspected safely.",
        )),
    }
}

fn prepare_program(path: &Path) -> SonaResult<PreparedProgram> {
    let extension = path.extension().and_then(|item| item.to_str());
    match extension {
        Some("sona") => {
            let source_bytes = fs::read(path).map_err(super::io_error)?;
            let source_text = String::from_utf8(source_bytes.clone()).map_err(|_| {
                super::io_error(io::Error::new(
                    io::ErrorKind::InvalidData,
                    "invalid UTF-8 source",
                ))
            })?;
            Ok(PreparedProgram {
                source: SourceFile::new(0, path.to_path_buf(), source_text),
                entry_path: path.to_path_buf(),
                identity: ProgramIdentity {
                    kind: "source",
                    container: None,
                    source_sha256: sha256_label(&source_bytes),
                    source_bytes: source_bytes.len() as u64,
                },
            })
        }
        Some("sbc") => {
            let container_bytes = fs::read(path).map_err(super::io_error)?;
            let payload =
                decode_source_backed_payload(&container_bytes, path.display().to_string())?;
            let source_text = String::from_utf8(payload.source_bytes.clone())
                .expect("validated source-backed payload");
            Ok(PreparedProgram {
                source: SourceFile::new(0, path.with_extension("sona"), source_text),
                entry_path: path.to_path_buf(),
                identity: ProgramIdentity {
                    kind: "sbc",
                    container: Some((sha256_label(&container_bytes), container_bytes.len() as u64)),
                    source_sha256: sha256_label(&payload.source_bytes),
                    source_bytes: payload.source_bytes.len() as u64,
                },
            })
        }
        _ => Err(proof_error(
            "PROOF-002",
            "E0001",
            "Unsupported Proof Mode input.",
            "Use a .sona source file or a validated source-backed .sbc container.",
        )),
    }
}

fn execute_prepared(
    prepared: PreparedProgram,
    capabilities: RuntimeCapabilities,
    target_key: &[u8],
) -> (NativeProofEvidence, Option<DiagnosticList>) {
    let mut evidence = NativeProofEvidence::new(target_key.to_vec());
    let result = (|| -> SonaResult<()> {
        let program = parse_source(&prepared.source)?;
        let bytecode = compile(lower(program)?, Some(prepared.source.text.clone()))?;
        let mut vm = Vm::new(Some(prepared.entry_path));
        vm.config.capabilities = capabilities;
        vm.enable_proof_observation(target_key.to_vec());
        let result = vm.execute(&bytecode).map(|_| ());
        evidence = vm
            .take_proof_evidence()
            .expect("Proof observation was enabled before execution");
        result
    })();
    (evidence, result.err())
}

fn build_receipt_for_program(
    version: &str,
    identity: &ProgramIdentity,
    capabilities: RuntimeCapabilities,
    duration_ms: u64,
    evidence: &NativeProofEvidence,
    program_error: Option<&DiagnosticList>,
    context: &ProofContext,
) -> SonaResult<Value> {
    if context.fault == Some(PersistenceFault::Serialization) {
        return Err(proof_error(
            "PROOF-006",
            "E0600",
            "Receipt serialization failed.",
            "Try the proof again; no receipt was published.",
        ));
    }
    let mut program = Map::new();
    program.insert("kind".to_string(), Value::String(identity.kind.to_string()));
    if let Some((hash, bytes)) = &identity.container {
        program.insert(
            "container".to_string(),
            json!({"sha256": hash, "bytes": bytes}),
        );
    }
    program.insert(
        "source".to_string(),
        json!({"sha256": identity.source_sha256, "bytes": identity.source_bytes}),
    );

    let effects = evidence
        .effects()
        .iter()
        .map(effect_json)
        .collect::<Vec<_>>();
    let diagnostic = program_error.and_then(execution_diagnostic_json);
    let receipt = json!({
        "schema_id": SCHEMA_ID,
        "schema": 1,
        "receipt_type": "native_execution_proof",
        "generated_at_utc": context.timestamp_utc,
        "sona_version": version,
        "engine": {
            "name": "native",
            "python_required": false,
            "python_embedded": false,
            "fallback_used": false
        },
        "program": Value::Object(program),
        "capabilities": {
            "console": capabilities.console,
            "filesystem_read": capabilities.filesystem_read,
            "filesystem_write": capabilities.filesystem_write,
            "network": capabilities.network,
            "process": capabilities.process,
            "environment": capabilities.environment
        },
        "execution": {
            "status": if program_error.is_some() { "failed" } else { "ok" },
            "exit_code": if program_error.is_some() { 1 } else { 0 },
            "duration_ms": duration_ms,
            "diagnostic": diagnostic,
            "stdout": {"sha256": evidence.stdout_sha256(), "bytes": evidence.stdout_bytes()},
            "stderr": {"sha256": evidence.stderr_sha256(), "bytes": evidence.stderr_bytes()}
        },
        "effects": effects
    });
    seal_receipt(receipt)
}

fn effect_json(effect: &NativeProofEffect) -> Value {
    let mut value = Map::new();
    value.insert("sequence".to_string(), json!(effect.sequence));
    value.insert("scope".to_string(), json!(effect.scope));
    value.insert("operation".to_string(), json!(effect.operation));
    value.insert("outcome".to_string(), json!(effect.outcome));
    if let Some(target) = &effect.target {
        value.insert("target".to_string(), json!(target));
    }
    Value::Object(value)
}

fn execution_diagnostic_json(diagnostics: &DiagnosticList) -> Option<Value> {
    let diagnostic = diagnostics.0.first()?;
    Some(json!({
        "id": diagnostic.diagnostic_id,
        "code": diagnostic.code,
        "category": diagnostic.category,
        "location": {
            "start_line": diagnostic.span.start_line,
            "start_column": diagnostic.span.start_column,
            "end_line": diagnostic.span.end_line,
            "end_column": diagnostic.span.end_column
        }
    }))
}

fn seal_receipt(mut receipt: Value) -> SonaResult<Value> {
    let hash_input = canonical_json(&receipt)?;
    let receipt_hash = sha256_label(&hash_input);
    let Value::Object(ref mut object) = receipt else {
        return Err(proof_error(
            "PROOF-006",
            "E0600",
            "Receipt serialization failed.",
            "Try the proof again; no receipt was published.",
        ));
    };
    object.insert("receipt_hash".to_string(), Value::String(receipt_hash));
    // Validate that the complete receipt is serializable before attempting any
    // filesystem operation.  `receipt_hash` is intentionally omitted only
    // from the first canonical encoding above.
    let _ = canonical_json(&receipt)?;
    Ok(receipt)
}

fn canonical_json(value: &Value) -> SonaResult<Vec<u8>> {
    serde_json::to_vec(value).map_err(|_| {
        proof_error(
            "PROOF-006",
            "E0600",
            "Receipt serialization failed.",
            "Try the proof again; no receipt was published.",
        )
    })
}

fn persist_receipt(
    destination: &Path,
    receipt: &Value,
    fault: Option<PersistenceFault>,
) -> SonaResult<()> {
    let bytes = canonical_json(receipt)?;
    let temporary = create_temporary_receipt(destination, fault)?;
    let temporary_path = temporary.1.clone();
    let mut file = temporary.0;
    let write_result = (|| -> io::Result<()> {
        file.write_all(&bytes)?;
        file.write_all(b"\n")?;
        file.flush()?;
        file.sync_all()?;
        Ok(())
    })();
    if write_result.is_err() || fault == Some(PersistenceFault::Finalization) {
        let _ = fs::remove_file(&temporary_path);
        return Err(proof_error(
            "PROOF-007",
            "E0600",
            "Receipt finalization failed.",
            "Do not treat the proof as published; inspect the destination before retrying.",
        ));
    }
    drop(file);

    match publish_no_clobber(&temporary_path, destination) {
        Ok(()) => {}
        Err((PublicationState::NotPublished, error))
            if error.kind() == io::ErrorKind::AlreadyExists =>
        {
            let _ = fs::remove_file(&temporary_path);
            return Err(proof_error(
                "PROOF-004",
                "E0601",
                "Receipt destination already exists.",
                "Provide a new, unused receipt path.",
            ));
        }
        Err((PublicationState::NotPublished, _)) => {
            let _ = fs::remove_file(&temporary_path);
            return Err(proof_error(
                "PROOF-007",
                "E0600",
                "Receipt finalization failed.",
                "Do not treat the proof as published; inspect the destination before retrying.",
            ));
        }
        Err((PublicationState::Published, _)) => {
            // The final receipt was atomically published.  Preserve it rather
            // than deleting evidence to conceal a later cleanup failure.
            return Err(proof_error(
                "PROOF-007",
                "E0600",
                "Receipt finalization failed.",
                "A receipt path may exist but is not publication-certified; inspect it before retrying.",
            ));
        }
    }
    if OpenOptions::new()
        .write(true)
        .open(destination)
        .and_then(|file| file.sync_all())
        .is_err()
    {
        // The final receipt was atomically published.  Preserve it rather
        // than deleting evidence to conceal a later durability failure.
        return Err(proof_error(
            "PROOF-007",
            "E0600",
            "Receipt finalization failed.",
            "A receipt path may exist but is not publication-certified; inspect it before retrying.",
        ));
    }
    Ok(())
}

fn publish_no_clobber(
    temporary_path: &Path,
    destination: &Path,
) -> Result<(), (PublicationState, io::Error)> {
    #[cfg(windows)]
    {
        // Windows rename is a no-replace publication when the destination is
        // absent, which preserves the receipt's evidence-creation contract.
        fs::rename(temporary_path, destination)
            .map_err(|error| (PublicationState::NotPublished, error))
    }
    #[cfg(not(windows))]
    {
        // POSIX rename may overwrite an existing file.  Hard-linking the
        // fully flushed temporary file publishes only when the final name is
        // absent, then removes the temporary alias.
        fs::hard_link(temporary_path, destination)
            .map_err(|error| (PublicationState::NotPublished, error))?;
        fs::remove_file(temporary_path).map_err(|error| (PublicationState::Published, error))
    }
}

fn create_temporary_receipt(
    destination: &Path,
    fault: Option<PersistenceFault>,
) -> SonaResult<(File, PathBuf)> {
    if fault == Some(PersistenceFault::Creation) {
        return Err(proof_error(
            "PROOF-005",
            "E0600",
            "Receipt creation failed.",
            "Check the receipt directory permissions and try a new path.",
        ));
    }
    let parent = destination
        .parent()
        .filter(|path| !path.as_os_str().is_empty())
        .unwrap_or_else(|| Path::new("."));
    let name = destination
        .file_name()
        .and_then(|item| item.to_str())
        .unwrap_or("receipt.json");
    for attempt in 0..32u32 {
        let nonce = format!(
            "{}-{}-{attempt}",
            std::process::id(),
            Utc::now().timestamp_nanos_opt().unwrap_or_default()
        );
        let temporary_path = parent.join(format!(".{name}.proof-{nonce}.tmp"));
        match OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(&temporary_path)
        {
            Ok(file) => return Ok((file, temporary_path)),
            Err(error) if error.kind() == io::ErrorKind::AlreadyExists => continue,
            Err(_) => break,
        }
    }
    Err(proof_error(
        "PROOF-005",
        "E0600",
        "Receipt creation failed.",
        "Check the receipt directory permissions and try a new path.",
    ))
}

fn proof_error(id: &str, code: &str, message: &str, hint: &str) -> DiagnosticList {
    DiagnosticList::single(Diagnostic::error(
        code,
        id,
        "proof",
        message,
        SourceSpan::unknown(),
        hint,
    ))
}

fn sha256_label(bytes: &[u8]) -> String {
    let digest = Sha256::digest(bytes);
    format!(
        "sha256:{}",
        digest
            .iter()
            .map(|byte| format!("{byte:02x}"))
            .collect::<String>()
    )
}

#[cfg(test)]
mod tests {
    use super::*;

    fn context(fault: Option<PersistenceFault>) -> ProofContext {
        ProofContext {
            timestamp_utc: "2026-08-08T00:00:00Z".to_string(),
            target_key: vec![7; 32],
            forced_duration_ms: Some(9),
            fault,
        }
    }

    #[test]
    fn proof_diagnostics_use_the_reserved_namespace() {
        let error = parse_invocation(&["proof".into()]).unwrap_err();
        assert_eq!(error.0[0].diagnostic_id, "PROOF-001");
        let error = prepare_program(Path::new("unsupported.txt")).unwrap_err();
        assert_eq!(error.0[0].diagnostic_id, "PROOF-002");
    }

    #[test]
    fn receipt_hash_uses_compact_canonical_bytes_without_newline() {
        let receipt = seal_receipt(json!({"z": 1, "a": ["first", "second"]})).unwrap();
        let hash = receipt["receipt_hash"].as_str().unwrap();
        let mut unsigned = receipt.clone();
        unsigned.as_object_mut().unwrap().remove("receipt_hash");
        let canonical = canonical_json(&unsigned).unwrap();
        assert_eq!(hash, sha256_label(&canonical));
        let mut with_newline = canonical;
        with_newline.push(b'\n');
        assert_ne!(hash, sha256_label(&with_newline));
    }

    #[test]
    fn injected_persistence_failures_are_proof_owned() {
        for (fault, expected) in [
            (PersistenceFault::Creation, "PROOF-005"),
            (PersistenceFault::Serialization, "PROOF-006"),
            (PersistenceFault::Finalization, "PROOF-007"),
        ] {
            let error = if fault == PersistenceFault::Serialization {
                build_receipt_for_program(
                    "0.15.4",
                    &ProgramIdentity {
                        kind: "source",
                        container: None,
                        source_sha256: "sha256:test".into(),
                        source_bytes: 1,
                    },
                    RuntimeCapabilities::default(),
                    0,
                    &NativeProofEvidence::new(vec![1; 32]),
                    None,
                    &context(Some(fault)),
                )
                .unwrap_err()
            } else {
                let directory =
                    std::env::temp_dir().join(format!("sona-proof-test-{}", std::process::id()));
                let _ = fs::create_dir_all(&directory);
                let path = directory.join("proof.json");
                let error = persist_receipt(
                    &path,
                    &seal_receipt(json!({"schema": 1})).unwrap(),
                    Some(fault),
                )
                .unwrap_err();
                let _ = fs::remove_dir_all(&directory);
                error
            };
            assert_eq!(error.0[0].diagnostic_id, expected);
        }
    }
}
