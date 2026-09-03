use std::collections::HashMap;
use std::fs::{self, OpenOptions};
use std::io::Write;
use std::path::{Path, PathBuf};
use std::thread;
use std::time::{Duration, SystemTime, UNIX_EPOCH};

use chrono::{Datelike, Local, NaiveDate, SecondsFormat, TimeZone, Utc};
use serde_json::Value as JsonValue;
use sona_diagnostics::{Diagnostic, DiagnosticList, SonaResult, SourceSpan};

use super::{values_equal, Value, Vm};

const MAX_FS_TEXT_BYTES: u64 = 16 * 1024 * 1024;

pub(super) fn module_exports(name: &str) -> Option<HashMap<String, Value>> {
    let entries: &[(&str, &str)] = match name {
        "collection" => &[
            ("first", "collection.first"),
            ("last", "collection.last"),
            ("take", "collection.take"),
            ("drop", "collection.drop"),
            ("flatten", "collection.flatten"),
            ("unique", "collection.unique"),
            ("frequencies", "collection.frequencies"),
            ("push", "collection.push"),
            ("pop", "collection.pop"),
        ],
        "date" => &[
            ("today", "date.today"),
            ("from_timestamp", "date.from_timestamp"),
            ("parse", "date.parse"),
            ("format", "date.format"),
        ],
        "fs" => &[
            ("read_text", "fs.read_text"),
            ("write_text", "fs.write_text"),
            ("append_text", "fs.append_text"),
            ("exists", "fs.exists"),
            ("is_file", "fs.is_file"),
            ("is_dir", "fs.is_dir"),
            ("list_dir", "fs.list_dir"),
            ("create_dir", "fs.create_dir"),
            ("remove", "fs.remove"),
            ("rename", "fs.rename"),
            ("copy", "fs.copy"),
            // Quiet compatibility aliases for the 0.15.x line.
            ("read", "fs.read_text"),
            ("write", "fs.write_text"),
            ("append", "fs.append_text"),
            ("mkdir", "fs.create_dir"),
        ],
        "http" => &[
            ("get", "http.get"),
            ("post", "http.post"),
            ("put", "http.put"),
            ("patch", "http.patch"),
            ("delete", "http.delete"),
        ],
        "io" => &[
            ("write_stdout", "io.write_stdout"),
            ("write_stderr", "io.write_stderr"),
            ("flush", "io.flush"),
        ],
        "json" => &[
            ("parse", "json.parse"),
            ("stringify", "json.stringify"),
            ("loads", "json.parse"),
            ("dumps", "json.stringify"),
        ],
        "math" => &[
            ("add", "math.add"),
            ("subtract", "math.subtract"),
            ("multiply", "math.multiply"),
            ("divide", "math.divide"),
            ("mod", "math.mod"),
            ("pow", "math.pow"),
            ("sqrt", "math.sqrt"),
            ("clamp", "math.clamp"),
            ("round", "math.round"),
            ("abs", "math.abs"),
            ("minimum", "math.minimum"),
            ("maximum", "math.maximum"),
        ],
        "random" => &[
            ("seed", "random.seed"),
            ("integer", "random.integer"),
            ("choice", "random.choice"),
            ("shuffle", "random.shuffle"),
            ("float", "random.float"),
            ("randint", "random.integer"),
            ("random", "random.float"),
        ],
        "stdin" => &[("read", "stdin.read")],
        "string" => &[
            ("length", "string.length"),
            ("upper", "string.upper"),
            ("lower", "string.lower"),
            ("trim", "string.trim"),
            ("split", "string.split"),
            ("join", "string.join"),
            ("replace", "string.replace"),
            ("contains", "string.contains"),
            ("starts_with", "string.starts_with"),
            ("ends_with", "string.ends_with"),
            ("startswith", "string.starts_with"),
            ("endswith", "string.ends_with"),
        ],
        "time" => &[
            ("now", "time.now"),
            ("timestamp", "time.timestamp"),
            ("monotonic", "time.monotonic"),
            ("sleep", "time.sleep"),
        ],
        _ => return None,
    };
    let mut exports = entries
        .iter()
        .map(|(export, function)| ((*export).to_string(), Value::NativeFunction(function)))
        .collect::<HashMap<_, _>>();
    if name == "math" {
        exports.insert("PI".to_string(), Value::Float(std::f64::consts::PI));
        exports.insert("TAU".to_string(), Value::Float(std::f64::consts::TAU));
        exports.insert("E".to_string(), Value::Float(std::f64::consts::E));
    }
    Some(exports)
}

impl Vm {
    pub(super) fn call_host(&mut self, name: &'static str, args: Vec<Value>) -> SonaResult<Value> {
        let result = match name {
            "collection.first" => collection_first(&args),
            "collection.last" => collection_last(&args),
            "collection.take" => collection_take(&args, false),
            "collection.drop" => collection_take(&args, true),
            "collection.flatten" => collection_flatten(&args),
            "collection.unique" => collection_unique(&args),
            "collection.frequencies" => collection_frequencies(&args),
            "collection.push" => collection_push(&args),
            "collection.pop" => collection_pop(&args),
            "date.today" => date_today(&args),
            "date.from_timestamp" => date_from_timestamp(&args),
            "date.parse" => date_parse(&args),
            "date.format" => date_format(&args),
            "fs.read_text" => self.fs_read_text(&args),
            "fs.write_text" => self.fs_write_text(&args, false),
            "fs.append_text" => self.fs_write_text(&args, true),
            "fs.exists" => self.fs_predicate(&args, "exists"),
            "fs.is_file" => self.fs_predicate(&args, "is_file"),
            "fs.is_dir" => self.fs_predicate(&args, "is_dir"),
            "fs.list_dir" => self.fs_list_dir(&args),
            "fs.create_dir" => self.fs_create_dir(&args),
            "fs.remove" => self.fs_remove(&args),
            "fs.rename" => self.fs_rename(&args),
            "fs.copy" => self.fs_copy(&args),
            name if name.starts_with("http.") => self.http_unavailable(name, &args),
            "io.write_stdout" => self.io_write(&args, false),
            "io.write_stderr" => self.io_write(&args, true),
            "io.flush" => self.io_flush(&args),
            "json.parse" => json_parse(&args),
            "json.stringify" => json_stringify(&args),
            name if name.starts_with("math.") => math_call(name, &args),
            "random.seed" => self.random_seed(&args),
            "random.integer" => self.random_integer(&args),
            "random.choice" => self.random_choice(&args),
            "random.shuffle" => self.random_shuffle(&args),
            "random.float" => self.random_float(&args),
            "stdin.read" => self.stdin_read(&args),
            name if name.starts_with("string.") => string_call(name, &args),
            "time.now" => time_now(&args),
            "time.timestamp" => time_timestamp(&args),
            "time.monotonic" => self.time_monotonic(&args),
            "time.sleep" => time_sleep(&args),
            _ => Err(stdlib_error(
                "E0104",
                "SONA-STDLIB-001",
                format!("Native host export '{name}' is not implemented."),
                "Use an export listed in the 0.15.5 native support matrix.",
            )),
        };
        self.record_host_effect(name, &args, &result);
        result
    }

    fn record_host_effect(&mut self, name: &str, args: &[Value], result: &SonaResult<Value>) {
        let diagnostic_id = result
            .as_ref()
            .err()
            .and_then(|items| items.0.first())
            .map(|diagnostic| diagnostic.diagnostic_id.as_str());
        let standard_outcome = if result.is_ok() {
            "allowed"
        } else if matches!(diagnostic_id, Some("SONA-FS-005") | Some("SONA-IO-003")) {
            "denied"
        } else {
            "failed"
        };

        match name {
            "fs.rename" | "fs.copy" => {
                let source = self.proof_filesystem_target(args.first());
                let destination = self.proof_filesystem_target(args.get(1));
                self.record_proof_effect(
                    "filesystem",
                    &format!("{name}.source"),
                    standard_outcome,
                    source,
                );
                self.record_proof_effect(
                    "filesystem",
                    &format!("{name}.destination"),
                    standard_outcome,
                    destination,
                );
            }
            name if name.starts_with("fs.") => {
                let target = self.proof_filesystem_target(args.first());
                self.record_proof_effect("filesystem", name, standard_outcome, target);
            }
            name if name.starts_with("http.") => {
                let outcome = if result.is_ok() {
                    "allowed"
                } else if self.config.capabilities.network {
                    "unavailable"
                } else {
                    "denied"
                };
                self.record_proof_effect("network", name, outcome, None);
            }
            "io.write_stdout" | "io.write_stderr" | "io.flush" => {
                self.record_proof_effect("console", name, standard_outcome, None);
            }
            "stdin.read" => {
                self.record_proof_effect("stdin", "read", standard_outcome, None);
            }
            "date.today" | "time.now" | "time.timestamp" | "time.monotonic" | "time.sleep" => {
                self.record_proof_effect("clock", name, standard_outcome, None);
            }
            "random.seed" | "random.integer" | "random.choice" | "random.shuffle"
            | "random.float" => {
                self.record_proof_effect("random", name, standard_outcome, None);
            }
            _ => {}
        }
    }

    fn require_fs(&self, write: bool) -> SonaResult<()> {
        let allowed = if write {
            self.config.capabilities.filesystem_write
        } else {
            self.config.capabilities.filesystem_read
        };
        if allowed {
            return Ok(());
        }
        Err(stdlib_error(
            "E0600",
            "SONA-FS-005",
            if write {
                "Native filesystem writes require --allow-fs-write."
            } else {
                "Native filesystem reads require --allow-fs-read."
            },
            "Grant only the filesystem capability required for this run.",
        ))
    }

    fn fs_read_text(&self, args: &[Value]) -> SonaResult<Value> {
        arity("fs.read_text", args, 1, 2)?;
        self.require_fs(false)?;
        require_utf8(args.get(1), "fs.read_text")?;
        let path = path_arg(args, 0, "fs.read_text")?;
        let metadata = fs::metadata(&path).map_err(|error| fs_error(error, "read_text"))?;
        if metadata.len() > MAX_FS_TEXT_BYTES {
            return Err(fs_limit_error("read_text"));
        }
        fs::read_to_string(path)
            .map(Value::String)
            .map_err(|error| fs_error(error, "read_text"))
    }

    fn fs_write_text(&self, args: &[Value], append: bool) -> SonaResult<Value> {
        let operation = if append {
            "fs.append_text"
        } else {
            "fs.write_text"
        };
        arity(operation, args, 2, 3)?;
        self.require_fs(true)?;
        require_utf8(args.get(2), operation)?;
        let path = path_arg(args, 0, operation)?;
        let content = string_arg(args, 1, operation)?;
        if content.len() as u64 > MAX_FS_TEXT_BYTES {
            return Err(fs_limit_error(operation));
        }
        if let Some(parent) = path.parent() {
            fs::create_dir_all(parent).map_err(|error| fs_error(error, operation))?;
        }
        let mut options = OpenOptions::new();
        options.create(true).write(true);
        if append {
            options.append(true);
        } else {
            options.truncate(true);
        }
        options
            .open(path)
            .and_then(|mut file| file.write_all(content.as_bytes()))
            .map_err(|error| fs_error(error, operation))?;
        Ok(Value::Int(content.chars().count() as i64))
    }

    fn fs_predicate(&self, args: &[Value], predicate: &str) -> SonaResult<Value> {
        arity(&format!("fs.{predicate}"), args, 1, 1)?;
        self.require_fs(false)?;
        let path = path_arg(args, 0, predicate)?;
        Ok(Value::Bool(match predicate {
            "exists" => path.exists(),
            "is_file" => path.is_file(),
            "is_dir" => path.is_dir(),
            _ => false,
        }))
    }

    fn fs_list_dir(&self, args: &[Value]) -> SonaResult<Value> {
        arity("fs.list_dir", args, 1, 1)?;
        self.require_fs(false)?;
        let path = path_arg(args, 0, "fs.list_dir")?;
        let mut entries = fs::read_dir(path)
            .map_err(|error| fs_error(error, "list_dir"))?
            .map(|entry| {
                entry
                    .map(|item| item.file_name().to_string_lossy().into_owned())
                    .map_err(|error| fs_error(error, "list_dir"))
            })
            .collect::<SonaResult<Vec<_>>>()?;
        entries.sort();
        Ok(Value::List(
            entries.into_iter().map(Value::String).collect(),
        ))
    }

    fn fs_create_dir(&self, args: &[Value]) -> SonaResult<Value> {
        arity("fs.create_dir", args, 1, 3)?;
        self.require_fs(true)?;
        let path = path_arg(args, 0, "fs.create_dir")?;
        let parents = optional_bool(args.get(1), true, "fs.create_dir")?;
        let result = if parents {
            fs::create_dir_all(&path)
        } else {
            fs::create_dir(&path)
        };
        result.map_err(|error| fs_error(error, "create_dir"))?;
        Ok(Value::String(normalize_path(&path)))
    }

    fn fs_remove(&self, args: &[Value]) -> SonaResult<Value> {
        arity("fs.remove", args, 1, 2)?;
        self.require_fs(true)?;
        let path = path_arg(args, 0, "fs.remove")?;
        if !path.exists() {
            return Ok(Value::Bool(false));
        }
        let recursive = optional_bool(args.get(1), true, "fs.remove")?;
        let result = if path.is_dir() {
            if recursive {
                fs::remove_dir_all(path)
            } else {
                fs::remove_dir(path)
            }
        } else {
            fs::remove_file(path)
        };
        result.map_err(|error| fs_error(error, "remove"))?;
        Ok(Value::Bool(true))
    }

    fn fs_rename(&self, args: &[Value]) -> SonaResult<Value> {
        arity("fs.rename", args, 2, 2)?;
        self.require_fs(true)?;
        let source = path_arg(args, 0, "fs.rename")?;
        let destination = path_arg(args, 1, "fs.rename")?;
        fs::rename(source, &destination).map_err(|error| fs_error(error, "rename"))?;
        Ok(Value::String(normalize_path(&destination)))
    }

    fn fs_copy(&self, args: &[Value]) -> SonaResult<Value> {
        arity("fs.copy", args, 2, 3)?;
        self.require_fs(false)?;
        self.require_fs(true)?;
        let source = path_arg(args, 0, "fs.copy")?;
        let destination = path_arg(args, 1, "fs.copy")?;
        let overwrite = optional_bool(args.get(2), true, "fs.copy")?;
        if destination.exists() {
            if !overwrite {
                return Err(fs_error(
                    std::io::Error::new(std::io::ErrorKind::AlreadyExists, "destination exists"),
                    "copy",
                ));
            }
            if destination.is_dir() {
                fs::remove_dir_all(&destination).map_err(|error| fs_error(error, "copy"))?;
            } else {
                fs::remove_file(&destination).map_err(|error| fs_error(error, "copy"))?;
            }
        }
        copy_path(&source, &destination).map_err(|error| fs_error(error, "copy"))?;
        Ok(Value::String(normalize_path(&destination)))
    }

    fn http_unavailable(&self, name: &str, args: &[Value]) -> SonaResult<Value> {
        arity(name, args, 1, 2)?;
        let message = if self.config.capabilities.network {
            "Native HTTP transport is unavailable in Sona 0.15.5."
        } else {
            "Native network access requires --allow-network."
        };
        Err(stdlib_error(
            "E0600",
            "SONA-HTTP-005",
            message,
            "Use Python compatibility for HTTP in 0.15.5 or grant network access in a future supported Native Core release.",
        ))
    }

    fn io_write(&mut self, args: &[Value], stderr: bool) -> SonaResult<Value> {
        arity(
            if stderr {
                "io.write_stderr"
            } else {
                "io.write_stdout"
            },
            args,
            1,
            1,
        )?;
        self.require_console()?;
        let text = args[0].to_string();
        if stderr {
            self.emit_stderr(&text).map_err(io_error)?;
        } else {
            self.emit_stdout(&text).map_err(io_error)?;
            self.output.push(text);
        }
        Ok(Value::Null)
    }

    fn io_flush(&self, args: &[Value]) -> SonaResult<Value> {
        arity("io.flush", args, 0, 0)?;
        self.require_console()?;
        std::io::stdout().flush().map_err(io_error)?;
        std::io::stderr().flush().map_err(io_error)?;
        Ok(Value::Null)
    }

    fn require_console(&self) -> SonaResult<()> {
        if self.config.capabilities.console {
            Ok(())
        } else {
            Err(stdlib_error(
                "E0600",
                "SONA-IO-003",
                "Console access is disabled by Native Core policy.",
                "Enable the console capability for this run.",
            ))
        }
    }

    fn stdin_read(&mut self, args: &[Value]) -> SonaResult<Value> {
        arity("stdin.read", args, 0, 1)?;
        self.require_console()?;
        if let Some(prompt) = args.first() {
            self.emit_stdout(&prompt.to_string()).map_err(io_error)?;
        }
        let mut line = String::new();
        std::io::stdin().read_line(&mut line).map_err(io_error)?;
        while line.ends_with(['\n', '\r']) {
            line.pop();
        }
        Ok(Value::String(line))
    }

    fn random_next(&mut self) -> u64 {
        self.random_state = self
            .random_state
            .wrapping_mul(6_364_136_223_846_793_005)
            .wrapping_add(1_442_695_040_888_963_407);
        self.random_state
    }

    fn random_seed(&mut self, args: &[Value]) -> SonaResult<Value> {
        arity("random.seed", args, 1, 1)?;
        self.random_state = int_arg(args, 0, "random.seed")? as u64;
        Ok(Value::Null)
    }

    fn random_float(&mut self, args: &[Value]) -> SonaResult<Value> {
        arity("random.float", args, 0, 0)?;
        let value = self.random_next() >> 11;
        Ok(Value::Float(value as f64 / (1u64 << 53) as f64))
    }

    fn random_integer(&mut self, args: &[Value]) -> SonaResult<Value> {
        arity("random.integer", args, 2, 2)?;
        let low = int_arg(args, 0, "random.integer")?;
        let high = int_arg(args, 1, "random.integer")?;
        if low > high {
            return Err(stdlib_error(
                "E0502",
                "SONA-STDLIB-002",
                "random.integer lower bound exceeds upper bound.",
                "Pass bounds in ascending order.",
            ));
        }
        let width = (high as i128 - low as i128 + 1) as u128;
        let offset = self.random_next() as u128 % width;
        Ok(Value::Int((low as i128 + offset as i128) as i64))
    }

    fn random_choice(&mut self, args: &[Value]) -> SonaResult<Value> {
        arity("random.choice", args, 1, 1)?;
        let items = list_arg(args, 0, "random.choice")?;
        if items.is_empty() {
            return Err(stdlib_error(
                "E0503",
                "SONA-STDLIB-002",
                "random.choice requires a non-empty list.",
                "Pass at least one item.",
            ));
        }
        let index = self.random_next() as usize % items.len();
        Ok(items[index].clone())
    }

    fn random_shuffle(&mut self, args: &[Value]) -> SonaResult<Value> {
        arity("random.shuffle", args, 1, 1)?;
        let mut items = list_arg(args, 0, "random.shuffle")?.clone();
        for index in (1..items.len()).rev() {
            let other = self.random_next() as usize % (index + 1);
            items.swap(index, other);
        }
        Ok(Value::List(items))
    }

    fn time_monotonic(&self, args: &[Value]) -> SonaResult<Value> {
        arity("time.monotonic", args, 0, 0)?;
        Ok(Value::Float(self.started_at.elapsed().as_secs_f64()))
    }
}

fn collection_first(args: &[Value]) -> SonaResult<Value> {
    arity("collection.first", args, 1, 2)?;
    Ok(list_arg(args, 0, "collection.first")?
        .first()
        .cloned()
        .or_else(|| args.get(1).cloned())
        .unwrap_or(Value::Null))
}

fn collection_last(args: &[Value]) -> SonaResult<Value> {
    arity("collection.last", args, 1, 2)?;
    Ok(list_arg(args, 0, "collection.last")?
        .last()
        .cloned()
        .or_else(|| args.get(1).cloned())
        .unwrap_or(Value::Null))
}

fn collection_take(args: &[Value], drop: bool) -> SonaResult<Value> {
    let name = if drop {
        "collection.drop"
    } else {
        "collection.take"
    };
    arity(name, args, 2, 2)?;
    let items = list_arg(args, 0, name)?;
    let count = int_arg(args, 1, name)?.max(0) as usize;
    let result = if drop {
        items.iter().skip(count).cloned().collect()
    } else {
        items.iter().take(count).cloned().collect()
    };
    Ok(Value::List(result))
}

fn collection_flatten(args: &[Value]) -> SonaResult<Value> {
    arity("collection.flatten", args, 1, 1)?;
    let mut result = Vec::new();
    for item in list_arg(args, 0, "collection.flatten")? {
        result.extend(list_value(item, "collection.flatten")?.iter().cloned());
    }
    Ok(Value::List(result))
}

fn collection_unique(args: &[Value]) -> SonaResult<Value> {
    arity("collection.unique", args, 1, 1)?;
    let mut result = Vec::new();
    for item in list_arg(args, 0, "collection.unique")? {
        if !result.iter().any(|seen| values_equal(seen, item)) {
            result.push(item.clone());
        }
    }
    Ok(Value::List(result))
}

fn collection_frequencies(args: &[Value]) -> SonaResult<Value> {
    arity("collection.frequencies", args, 1, 1)?;
    let mut result = HashMap::new();
    for item in list_arg(args, 0, "collection.frequencies")? {
        let key = item.to_string();
        let count = match result.get(&key) {
            Some(Value::Int(value)) => value + 1,
            _ => 1,
        };
        result.insert(key, Value::Int(count));
    }
    Ok(Value::Map(result))
}

fn collection_push(args: &[Value]) -> SonaResult<Value> {
    arity("collection.push", args, 2, 2)?;
    let mut result = list_arg(args, 0, "collection.push")?.clone();
    result.push(args[1].clone());
    Ok(Value::List(result))
}

fn collection_pop(args: &[Value]) -> SonaResult<Value> {
    arity("collection.pop", args, 1, 2)?;
    let items = list_arg(args, 0, "collection.pop")?;
    if items.is_empty() {
        return Err(stdlib_error(
            "E0503",
            "SONA-STDLIB-002",
            "collection.pop requires a non-empty list.",
            "Check the list before popping.",
        ));
    }
    let index = if args.len() == 2 {
        let value = int_arg(args, 1, "collection.pop")?;
        if value < 0 {
            items.len() as i64 + value
        } else {
            value
        }
    } else {
        items.len() as i64 - 1
    };
    items.get(index as usize).cloned().ok_or_else(|| {
        stdlib_error(
            "E0302",
            "SONA-STDLIB-002",
            "collection.pop index is out of range.",
            "Use an index present in the list.",
        )
    })
}

fn json_parse(args: &[Value]) -> SonaResult<Value> {
    arity("json.parse", args, 1, 1)?;
    let source = string_arg(args, 0, "json.parse")?;
    let value: JsonValue = serde_json::from_str(source).map_err(|_| {
        stdlib_error(
            "E0501",
            "SONA-JSON-001",
            "JSON parsing failed.",
            "Provide valid JSON text.",
        )
    })?;
    json_to_value(value)
}

fn json_stringify(args: &[Value]) -> SonaResult<Value> {
    arity("json.stringify", args, 1, 2)?;
    let indent = match args.get(1) {
        None | Some(Value::Null) => None,
        Some(Value::Int(value)) if *value >= 0 => Some(*value as usize),
        _ => {
            return Err(stdlib_error(
                "E0501",
                "SONA-JSON-003",
                "JSON indentation must be nil or a non-negative integer.",
                "Use nil, 0, 2, or another non-negative integer.",
            ))
        }
    };
    let mut output = String::new();
    stringify_value(&args[0], indent, 0, &mut output)?;
    Ok(Value::String(output))
}

fn stringify_value(
    value: &Value,
    indent: Option<usize>,
    depth: usize,
    output: &mut String,
) -> SonaResult<()> {
    match value {
        Value::Null => output.push_str("null"),
        Value::Bool(value) => output.push_str(if *value { "true" } else { "false" }),
        Value::Int(value) => output.push_str(&value.to_string()),
        Value::Float(value) if value.is_finite() => output.push_str(&value.to_string()),
        Value::String(value) => {
            output.push_str(&serde_json::to_string(value).map_err(json_serialize_error)?)
        }
        Value::List(items) => {
            output.push('[');
            for (index, item) in items.iter().enumerate() {
                if index > 0 {
                    output.push(',');
                    if indent.is_none() {
                        output.push(' ');
                    }
                }
                pretty_break(indent, depth + 1, output);
                stringify_value(item, indent, depth + 1, output)?;
            }
            if !items.is_empty() {
                pretty_break(indent, depth, output);
            }
            output.push(']');
        }
        Value::Map(items) => {
            output.push('{');
            let mut keys = items.keys().collect::<Vec<_>>();
            keys.sort();
            for (index, key) in keys.iter().enumerate() {
                if index > 0 {
                    output.push(',');
                    if indent.is_none() {
                        output.push(' ');
                    }
                }
                pretty_break(indent, depth + 1, output);
                output.push_str(&serde_json::to_string(key).map_err(json_serialize_error)?);
                output.push(':');
                output.push(' ');
                stringify_value(&items[*key], indent, depth + 1, output)?;
            }
            if !items.is_empty() {
                pretty_break(indent, depth, output);
            }
            output.push('}');
        }
        _ => return Err(json_serialize_error("non-JSON runtime value")),
    }
    Ok(())
}

fn pretty_break(indent: Option<usize>, depth: usize, output: &mut String) {
    if let Some(width) = indent {
        output.push('\n');
        output.push_str(&" ".repeat(width.saturating_mul(depth)));
    }
}

fn json_serialize_error(_error: impl std::fmt::Display) -> DiagnosticList {
    stdlib_error(
        "E0200",
        "SONA-JSON-002",
        "JSON serialization failed.",
        "Pass a JSON-compatible value.",
    )
}

fn json_to_value(value: JsonValue) -> SonaResult<Value> {
    Ok(match value {
        JsonValue::Null => Value::Null,
        JsonValue::Bool(value) => Value::Bool(value),
        JsonValue::Number(value) => {
            if let Some(integer) = value.as_i64() {
                Value::Int(integer)
            } else {
                Value::Float(value.as_f64().ok_or_else(json_number_error)?)
            }
        }
        JsonValue::String(value) => Value::String(value),
        JsonValue::Array(items) => Value::List(
            items
                .into_iter()
                .map(json_to_value)
                .collect::<SonaResult<Vec<_>>>()?,
        ),
        JsonValue::Object(items) => Value::Map(
            items
                .into_iter()
                .map(|(key, value)| Ok((key, json_to_value(value)?)))
                .collect::<SonaResult<HashMap<_, _>>>()?,
        ),
    })
}

fn json_number_error() -> DiagnosticList {
    stdlib_error(
        "E0501",
        "SONA-JSON-001",
        "JSON number is outside the Native Core range.",
        "Use a finite number supported by the native runtime.",
    )
}

fn math_call(name: &str, args: &[Value]) -> SonaResult<Value> {
    let unary = |operation: fn(f64) -> f64| -> SonaResult<Value> {
        arity(name, args, 1, 1)?;
        Ok(Value::Float(operation(number_arg(args, 0, name)?)))
    };
    let binary = |operation: fn(f64, f64) -> f64| -> SonaResult<Value> {
        arity(name, args, 2, 2)?;
        Ok(Value::Float(operation(
            number_arg(args, 0, name)?,
            number_arg(args, 1, name)?,
        )))
    };
    match name {
        "math.add" => binary(|a, b| a + b),
        "math.subtract" => binary(|a, b| a - b),
        "math.multiply" => binary(|a, b| a * b),
        "math.divide" | "math.mod" => {
            arity(name, args, 2, 2)?;
            let left = number_arg(args, 0, name)?;
            let right = number_arg(args, 1, name)?;
            if right == 0.0 {
                return Err(stdlib_error(
                    "E0301",
                    "SONA-STDLIB-002",
                    "Division or modulo by zero.",
                    "Use a nonzero divisor.",
                ));
            }
            Ok(Value::Float(if name == "math.divide" {
                left / right
            } else {
                left % right
            }))
        }
        "math.pow" => binary(f64::powf),
        "math.sqrt" => {
            arity(name, args, 1, 1)?;
            let value = number_arg(args, 0, name)?;
            if value < 0.0 {
                return Err(stdlib_error(
                    "E0501",
                    "SONA-STDLIB-002",
                    "Square root domain error.",
                    "Pass a non-negative number.",
                ));
            }
            Ok(Value::Float(value.sqrt()))
        }
        "math.clamp" => {
            arity(name, args, 3, 3)?;
            let value = number_arg(args, 0, name)?;
            let low = number_arg(args, 1, name)?;
            let high = number_arg(args, 2, name)?;
            if low > high {
                return Err(stdlib_error(
                    "E0501",
                    "SONA-STDLIB-002",
                    "Clamp lower bound exceeds upper bound.",
                    "Pass bounds in ascending order.",
                ));
            }
            Ok(Value::Float(value.clamp(low, high)))
        }
        "math.round" => {
            arity(name, args, 1, 2)?;
            let value = number_arg(args, 0, name)?;
            let digits = match args.get(1) {
                Some(Value::Int(value)) => *value as i32,
                None | Some(Value::Null) => 0,
                _ => return Err(type_argument(name)),
            };
            let factor = 10f64.powi(digits);
            Ok(Value::Float((value * factor).round_ties_even() / factor))
        }
        "math.abs" => unary(f64::abs),
        "math.minimum" | "math.maximum" => {
            arity(name, args, 1, 1)?;
            let items = list_arg(args, 0, name)?;
            if items.is_empty() {
                return Err(stdlib_error(
                    "E0503",
                    "SONA-STDLIB-002",
                    "Minimum/maximum requires a non-empty list.",
                    "Pass at least one number.",
                ));
            }
            let mut values = items.iter().map(|item| number_value(item, name));
            let first = values.next().expect("non-empty checked")?;
            let result = values.try_fold(first, |current, value| {
                let next = value?;
                Ok::<_, DiagnosticList>(if name == "math.minimum" {
                    current.min(next)
                } else {
                    current.max(next)
                })
            })?;
            Ok(Value::Float(result))
        }
        _ => Err(type_argument(name)),
    }
}

fn string_call(name: &str, args: &[Value]) -> SonaResult<Value> {
    match name {
        "string.length" => {
            arity(name, args, 1, 1)?;
            Ok(Value::Int(string_arg(args, 0, name)?.chars().count() as i64))
        }
        "string.upper" => unary_string(name, args, |value| value.to_uppercase()),
        "string.lower" => unary_string(name, args, |value| value.to_lowercase()),
        "string.trim" => unary_string(name, args, |value| value.trim().to_string()),
        "string.contains" | "string.starts_with" | "string.ends_with" => {
            arity(name, args, 2, 2)?;
            let value = string_arg(args, 0, name)?;
            let needle = string_arg(args, 1, name)?;
            Ok(Value::Bool(match name {
                "string.contains" => value.contains(needle),
                "string.starts_with" => value.starts_with(needle),
                _ => value.ends_with(needle),
            }))
        }
        "string.split" => {
            arity(name, args, 1, 2)?;
            let value = string_arg(args, 0, name)?;
            let parts: Vec<String> = match args.get(1) {
                None | Some(Value::Null) => value.split_whitespace().map(str::to_string).collect(),
                Some(Value::String(delimiter)) => {
                    value.split(delimiter).map(str::to_string).collect()
                }
                _ => return Err(type_argument(name)),
            };
            Ok(Value::List(parts.into_iter().map(Value::String).collect()))
        }
        "string.join" => {
            arity(name, args, 1, 2)?;
            let items = list_arg(args, 0, name)?;
            let delimiter = match args.get(1) {
                None | Some(Value::Null) => "",
                Some(Value::String(value)) => value,
                _ => return Err(type_argument(name)),
            };
            Ok(Value::String(
                items
                    .iter()
                    .map(ToString::to_string)
                    .collect::<Vec<_>>()
                    .join(delimiter),
            ))
        }
        "string.replace" => {
            arity(name, args, 3, 4)?;
            let value = string_arg(args, 0, name)?;
            let old = string_arg(args, 1, name)?;
            let new = string_arg(args, 2, name)?;
            let result = match args.get(3) {
                None | Some(Value::Null) => value.replace(old, new),
                Some(Value::Int(count)) if *count >= 0 => value.replacen(old, new, *count as usize),
                _ => return Err(type_argument(name)),
            };
            Ok(Value::String(result))
        }
        _ => Err(type_argument(name)),
    }
}

fn unary_string(
    name: &str,
    args: &[Value],
    operation: impl FnOnce(&str) -> String,
) -> SonaResult<Value> {
    arity(name, args, 1, 1)?;
    Ok(Value::String(operation(string_arg(args, 0, name)?)))
}

fn time_now(args: &[Value]) -> SonaResult<Value> {
    arity("time.now", args, 0, 2)?;
    Ok(Value::String(
        Local::now().to_rfc3339_opts(SecondsFormat::Secs, false),
    ))
}

fn time_timestamp(args: &[Value]) -> SonaResult<Value> {
    arity("time.timestamp", args, 0, 0)?;
    let value = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map_err(|_| time_error("System time precedes the Unix epoch."))?;
    Ok(Value::Float(value.as_secs_f64()))
}

fn time_sleep(args: &[Value]) -> SonaResult<Value> {
    arity("time.sleep", args, 1, 1)?;
    let seconds = number_arg(args, 0, "time.sleep")?;
    if !seconds.is_finite() || !(0.0..=86_400.0).contains(&seconds) {
        return Err(time_error(
            "Sleep duration must be finite and between 0 and 86400 seconds.",
        ));
    }
    thread::sleep(Duration::from_secs_f64(seconds));
    Ok(Value::Null)
}

fn date_today(args: &[Value]) -> SonaResult<Value> {
    arity("date.today", args, 0, 1)?;
    let utc = matches!(args.first(), Some(Value::String(value)) if value.eq_ignore_ascii_case("utc") || value.eq_ignore_ascii_case("z"));
    let result = if utc {
        Utc::now().date_naive()
    } else {
        Local::now().date_naive()
    };
    Ok(Value::String(result.format("%Y-%m-%d").to_string()))
}

fn date_from_timestamp(args: &[Value]) -> SonaResult<Value> {
    arity("date.from_timestamp", args, 1, 2)?;
    let timestamp = number_arg(args, 0, "date.from_timestamp")?;
    let seconds = timestamp.floor() as i64;
    let nanos = ((timestamp - seconds as f64) * 1_000_000_000.0).round() as u32;
    let utc = Utc
        .timestamp_opt(seconds, nanos)
        .single()
        .ok_or_else(|| time_error("Timestamp is outside the supported range."))?;
    let use_utc = matches!(args.get(1), Some(Value::String(value)) if value.eq_ignore_ascii_case("utc") || value.eq_ignore_ascii_case("z"));
    let result = if use_utc {
        utc.date_naive()
    } else {
        utc.with_timezone(&Local).date_naive()
    };
    Ok(Value::String(result.format("%Y-%m-%d").to_string()))
}

fn parse_date(value: &str) -> SonaResult<NaiveDate> {
    NaiveDate::parse_from_str(value.get(..10).unwrap_or(value), "%Y-%m-%d")
        .map_err(|_| time_error("Date parsing failed; expected ISO YYYY-MM-DD input."))
}

fn date_parse(args: &[Value]) -> SonaResult<Value> {
    arity("date.parse", args, 1, 2)?;
    let date = parse_date(string_arg(args, 0, "date.parse")?)?;
    let mut result = HashMap::new();
    result.insert(
        "iso".to_string(),
        Value::String(date.format("%Y-%m-%d").to_string()),
    );
    result.insert("year".to_string(), Value::Int(date.year() as i64));
    result.insert("month".to_string(), Value::Int(date.month() as i64));
    result.insert("day".to_string(), Value::Int(date.day() as i64));
    result.insert(
        "weekday".to_string(),
        Value::Int(date.weekday().number_from_monday() as i64),
    );
    result.insert(
        "iso_week".to_string(),
        Value::Int(date.iso_week().week() as i64),
    );
    result.insert(
        "iso_year".to_string(),
        Value::Int(date.iso_week().year() as i64),
    );
    result.insert(
        "quarter".to_string(),
        Value::Int(((date.month() - 1) / 3 + 1) as i64),
    );
    result.insert("day_of_year".to_string(), Value::Int(date.ordinal() as i64));
    result.insert(
        "is_leap_year".to_string(),
        Value::Bool(NaiveDate::from_ymd_opt(date.year(), 2, 29).is_some()),
    );
    Ok(Value::Map(result))
}

fn date_format(args: &[Value]) -> SonaResult<Value> {
    arity("date.format", args, 2, 3)?;
    let date = parse_date(string_arg(args, 0, "date.format")?)?;
    let pattern = string_arg(args, 1, "date.format")?;
    Ok(Value::String(date.format(pattern).to_string()))
}

fn arity(name: &str, args: &[Value], minimum: usize, maximum: usize) -> SonaResult<()> {
    if (minimum..=maximum).contains(&args.len()) {
        return Ok(());
    }
    Err(stdlib_error(
        "E0300",
        "SONA-NATIVE-RUNTIME-001",
        format!(
            "{name} expects {minimum}..={maximum} arguments; received {}.",
            args.len()
        ),
        "Pass the documented arguments for this standard-library export.",
    ))
}

fn string_arg<'a>(args: &'a [Value], index: usize, name: &str) -> SonaResult<&'a str> {
    match args.get(index) {
        Some(Value::String(value)) => Ok(value),
        _ => Err(type_argument(name)),
    }
}

fn path_arg(args: &[Value], index: usize, name: &str) -> SonaResult<PathBuf> {
    let value = string_arg(args, index, name)?;
    if value.is_empty() || value.contains('\0') {
        return Err(stdlib_error(
            "E0501",
            "SONA-FS-001",
            "Filesystem path is invalid.",
            "Pass a non-empty path without null characters.",
        ));
    }
    Ok(PathBuf::from(value))
}

fn int_arg(args: &[Value], index: usize, name: &str) -> SonaResult<i64> {
    match args.get(index) {
        Some(Value::Int(value)) => Ok(*value),
        _ => Err(type_argument(name)),
    }
}

fn number_arg(args: &[Value], index: usize, name: &str) -> SonaResult<f64> {
    args.get(index).map_or_else(
        || Err(type_argument(name)),
        |value| number_value(value, name),
    )
}

fn number_value(value: &Value, name: &str) -> SonaResult<f64> {
    match value {
        Value::Int(value) => Ok(*value as f64),
        Value::Float(value) => Ok(*value),
        _ => Err(type_argument(name)),
    }
}

fn list_arg<'a>(args: &'a [Value], index: usize, name: &str) -> SonaResult<&'a Vec<Value>> {
    args.get(index)
        .map_or_else(|| Err(type_argument(name)), |value| list_value(value, name))
}

fn list_value<'a>(value: &'a Value, name: &str) -> SonaResult<&'a Vec<Value>> {
    match value {
        Value::List(items) => Ok(items),
        _ => Err(type_argument(name)),
    }
}

fn optional_bool(value: Option<&Value>, default: bool, name: &str) -> SonaResult<bool> {
    match value {
        None | Some(Value::Null) => Ok(default),
        Some(Value::Bool(value)) => Ok(*value),
        _ => Err(type_argument(name)),
    }
}

fn require_utf8(value: Option<&Value>, name: &str) -> SonaResult<()> {
    match value {
        None | Some(Value::Null) => Ok(()),
        Some(Value::String(value))
            if value.eq_ignore_ascii_case("utf-8") || value.eq_ignore_ascii_case("utf8") =>
        {
            Ok(())
        }
        _ => Err(stdlib_error(
            "E0603",
            "SONA-FS-006",
            format!("{name} requires UTF-8 text."),
            "Use encoding='utf-8'.",
        )),
    }
}

fn type_argument(name: &str) -> DiagnosticList {
    stdlib_error(
        "E0200",
        "SONA-STDLIB-002",
        format!("{name} received an argument with an unsupported type."),
        "Pass values matching the documented signature.",
    )
}

fn stdlib_error(code: &str, id: &str, message: impl Into<String>, hint: &str) -> DiagnosticList {
    DiagnosticList::single(Diagnostic::error(
        code,
        id,
        "stdlib",
        message,
        SourceSpan::unknown(),
        hint,
    ))
}

fn fs_error(error: std::io::Error, operation: &str) -> DiagnosticList {
    use std::io::ErrorKind;
    let (code, id, message, hint) = match error.kind() {
        ErrorKind::NotFound => (
            "E0601",
            "SONA-FS-002",
            "Filesystem path was not found.",
            "Verify the path and run the operation again.",
        ),
        ErrorKind::PermissionDenied => (
            "E0602",
            "SONA-FS-004",
            "Filesystem permission was denied.",
            "Verify that the process has the required access.",
        ),
        ErrorKind::InvalidData => (
            "E0603",
            "SONA-FS-006",
            "Filesystem text was not valid UTF-8.",
            "Use UTF-8 text.",
        ),
        _ => (
            "E0600",
            "SONA-FS-003",
            "Filesystem operation failed.",
            "Check the path, available space, and operating-system error.",
        ),
    };
    stdlib_error(
        code,
        id,
        format!("{message} (operation=fs.{operation})"),
        hint,
    )
}

fn fs_limit_error(operation: &str) -> DiagnosticList {
    stdlib_error(
        "E0502",
        "SONA-FS-003",
        format!("Filesystem text limit exceeded. (operation=fs.{operation})"),
        "Use a file no larger than 16 MiB in the Native Core preview.",
    )
}

fn io_error(_error: std::io::Error) -> DiagnosticList {
    stdlib_error(
        "E0600",
        "SONA-IO-002",
        "Console output failed.",
        "Verify that the output stream is available.",
    )
}

fn time_error(message: &str) -> DiagnosticList {
    stdlib_error(
        "E0501",
        "SONA-TIME-001",
        message,
        "Pass a supported date, time, or duration value.",
    )
}

fn normalize_path(path: &Path) -> String {
    path.to_string_lossy().replace('\\', "/")
}

fn copy_path(source: &Path, destination: &Path) -> std::io::Result<()> {
    if source.is_dir() {
        fs::create_dir_all(destination)?;
        for entry in fs::read_dir(source)? {
            let entry = entry?;
            copy_path(&entry.path(), &destination.join(entry.file_name()))?;
        }
    } else {
        if let Some(parent) = destination.parent() {
            fs::create_dir_all(parent)?;
        }
        fs::copy(source, destination)?;
    }
    Ok(())
}
