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
    PostPublication,
}

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

#[derive(Debug)]
struct ProofFailure {
    surfaced: DiagnosticList,
    program: Option<DiagnosticList>,
}

impl ProofFailure {
    fn infrastructure(surfaced: DiagnosticList) -> Self {
        Self {
            surfaced,
            program: None,
        }
    }

    fn after_execution(surfaced: DiagnosticList, program: &Option<DiagnosticList>) -> Self {
        Self {
            surfaced,
            program: program.clone(),
        }
    }
}

impl From<DiagnosticList> for ProofFailure {
    fn from(value: DiagnosticList) -> Self {
        Self::infrastructure(value)
    }
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
    run_with_context(args, version, None).map_err(|failure| {
        let ProofFailure { surfaced, program } = failure;
        // The program diagnostic is intentionally retained through the Proof
        // boundary for internal tests/debugging, then omitted from public
        // output when a Proof infrastructure diagnostic takes precedence.
        drop(program);
        surfaced
    })
}

fn run_with_context(
    args: &[String],
    version: &str,
    supplied_context: Option<ProofContext>,
) -> Result<i32, ProofFailure> {
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
    )
    .map_err(|failure| ProofFailure::after_execution(failure, &program_error))?;
    persist_receipt(&receipt_path, &receipt, context.fault)
        .map_err(|failure| ProofFailure::after_execution(failure, &program_error))?;

    if let Some(diagnostics) = program_error {
        return Err(ProofFailure {
            program: Some(diagnostics.clone()),
            surfaced: diagnostics,
        });
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
    let invalid =
        |hint: &str| proof_error("PROOF-001", "E0001", "Invalid Proof Mode invocation.", hint);
    let mut receipt = None;
    let mut engine_seen = false;
    let mut index = 2;
    while index < args.len() {
        match args[index].as_str() {
            "--receipt" => {
                if receipt.is_some() {
                    return Err(invalid("Provide exactly one --receipt <path> option."));
                }
                let Some(value) = args.get(index + 1) else {
                    return Err(invalid("Provide a path after --receipt."));
                };
                if value.is_empty() || value.starts_with('-') {
                    return Err(invalid("Provide a non-option path after --receipt."));
                }
                receipt = Some(PathBuf::from(value));
                index += 2;
            }
            "--engine" => {
                if engine_seen {
                    return Err(invalid("Provide at most one --engine option."));
                }
                let Some(value) = args.get(index + 1) else {
                    return Err(invalid("Provide a value after --engine."));
                };
                if value.is_empty() || value.starts_with('-') {
                    return Err(invalid("Provide a non-option value after --engine."));
                }
                engine_seen = true;
                index += 2;
            }
            "--allow-fs-read" | "--allow-fs-write" | "--allow-network" => {
                index += 1;
            }
            option if option.starts_with('-') => {
                return Err(invalid("Use only documented Proof Mode options."));
            }
            _ => {
                return Err(invalid(
                    "Provide one program path followed only by Proof Mode options.",
                ));
            }
        }
    }
    let Some(receipt) = receipt else {
        return Err(invalid("Provide exactly one --receipt <path> option."));
    };
    Ok((PathBuf::from(target), receipt))
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
        drop(file);
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
    if fault == Some(PersistenceFault::PostPublication) {
        return Err(proof_error(
            "PROOF-007",
            "E0600",
            "Receipt finalization failed.",
            "A receipt path may exist but is not publication-certified; inspect it before retrying.",
        ));
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
    // `rename` may replace an existing destination on both Windows and POSIX.
    // A same-directory hard link is an atomic create-if-absent publication;
    // unsupported filesystems fail closed instead of weakening no-clobber.
    fs::hard_link(temporary_path, destination)
        .map_err(|error| (PublicationState::NotPublished, error))?;
    fs::remove_file(temporary_path).map_err(|error| (PublicationState::Published, error))
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
    fn malformed_proof_arguments_are_rejected() {
        for args in [
            vec![
                "proof".into(),
                "app.sona".into(),
                "unexpected".into(),
                "--receipt".into(),
                "proof.json".into(),
            ],
            vec![
                "proof".into(),
                "app.sona".into(),
                "--unknown".into(),
                "--receipt".into(),
                "proof.json".into(),
            ],
            vec![
                "proof".into(),
                "app.sona".into(),
                "--receipt".into(),
                "proof.json".into(),
                "--engine".into(),
            ],
        ] {
            let error = parse_invocation(&args).unwrap_err();
            assert_eq!(error.0[0].diagnostic_id, "PROOF-001");
        }
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

    #[test]
    fn prepublication_failure_removes_its_temporary_receipt() {
        let directory =
            std::env::temp_dir().join(format!("sona-proof-cleanup-{}", std::process::id()));
        let _ = fs::remove_dir_all(&directory);
        fs::create_dir_all(&directory).unwrap();
        let destination = directory.join("proof.json");
        let error = persist_receipt(
            &destination,
            &seal_receipt(json!({"schema": 1})).unwrap(),
            Some(PersistenceFault::Finalization),
        )
        .unwrap_err();
        assert_eq!(error.0[0].diagnostic_id, "PROOF-007");
        assert!(!destination.exists());
        assert_eq!(fs::read_dir(&directory).unwrap().count(), 0);
        fs::remove_dir_all(directory).unwrap();
    }

    #[test]
    fn publication_never_clobbers_an_existing_destination() {
        let directory =
            std::env::temp_dir().join(format!("sona-proof-no-clobber-{}", std::process::id()));
        let _ = fs::remove_dir_all(&directory);
        fs::create_dir_all(&directory).unwrap();
        let temporary = directory.join("temporary.json");
        let destination = directory.join("proof.json");
        fs::write(&temporary, b"new evidence\n").unwrap();
        fs::write(&destination, b"existing evidence\n").unwrap();

        let result = publish_no_clobber(&temporary, &destination);
        assert!(result.is_err());
        assert_eq!(fs::read(&destination).unwrap(), b"existing evidence\n");
        assert_eq!(fs::read(&temporary).unwrap(), b"new evidence\n");

        fs::remove_dir_all(directory).unwrap();
    }

    #[test]
    fn postpublication_failure_preserves_the_uncertified_receipt() {
        let directory = std::env::temp_dir().join(format!(
            "sona-proof-post-publication-{}",
            std::process::id()
        ));
        let _ = fs::remove_dir_all(&directory);
        fs::create_dir_all(&directory).unwrap();
        let destination = directory.join("proof.json");
        let receipt = seal_receipt(json!({"schema": 1})).unwrap();

        let error = persist_receipt(
            &destination,
            &receipt,
            Some(PersistenceFault::PostPublication),
        )
        .unwrap_err();
        assert_eq!(error.0[0].diagnostic_id, "PROOF-007");
        assert!(destination.exists());
        let mut expected = canonical_json(&receipt).unwrap();
        expected.push(b'\n');
        assert_eq!(fs::read(&destination).unwrap(), expected);
        assert_eq!(fs::read_dir(&directory).unwrap().count(), 1);

        fs::remove_dir_all(directory).unwrap();
    }

    #[test]
    fn persistence_failure_retains_the_program_diagnostic_internally() {
        let directory =
            std::env::temp_dir().join(format!("sona-proof-precedence-{}", std::process::id()));
        let _ = fs::remove_dir_all(&directory);
        fs::create_dir_all(&directory).unwrap();
        let source = directory.join("invalid.sona");
        fs::write(&source, "fn legacy() { return 1; };\n").unwrap();
        let destination = directory.join("proof.json");
        let args = vec![
            "proof".into(),
            source.to_string_lossy().into_owned(),
            "--receipt".into(),
            destination.to_string_lossy().into_owned(),
        ];

        let failure = run_with_context(
            &args,
            "0.15.4",
            Some(context(Some(PersistenceFault::Finalization))),
        )
        .unwrap_err();
        assert_eq!(failure.surfaced.0[0].diagnostic_id, "PROOF-007");
        assert_eq!(
            failure.program.as_ref().unwrap().0[0].diagnostic_id,
            "SONA-PARSE-001"
        );
        assert!(!destination.exists());

        fs::remove_dir_all(directory).unwrap();
    }
}
