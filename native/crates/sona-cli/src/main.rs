use std::env;
use std::fs;
use std::path::{Path, PathBuf};

use sona_bytecode::{compile, decode_source_backed, encode_source_backed, BYTECODE_VERSION};
use sona_diagnostics::{DiagnosticList, SonaResult};
use sona_ir::lower;
use sona_lexer::lex;
use sona_parser::parse_source;
use sona_source::SourceFile;
use sona_vm::Vm;

const VERSION: &str = env!("CARGO_PKG_VERSION");

fn main() {
    let code = match run(env::args().skip(1).collect()) {
        Ok(code) => code,
        Err(diagnostics) => {
            eprintln!("{diagnostics}");
            1
        }
    };
    std::process::exit(code);
}

fn run(args: Vec<String>) -> SonaResult<i32> {
    if args.is_empty() || args[0] == "--help" || args[0] == "-h" {
        print_help();
        return Ok(0);
    }
    if args[0] == "--version" || args[0] == "-v" {
        println!("Sona native {VERSION}");
        return Ok(0);
    }
    match args[0].as_str() {
        "run" => {
            let file = positional(&args, 1, "run requires a .sona file")?;
            require_native_engine(&args)?;
            run_file(Path::new(file))?;
            Ok(0)
        }
        "check" => {
            let file = positional(&args, 1, "check requires a .sona file")?;
            require_native_engine(&args)?;
            check_file(Path::new(file))?;
            println!("ok");
            Ok(0)
        }
        "compile" => {
            let file = positional(&args, 1, "compile requires a .sona file")?;
            let output = option_value(&args, "--output").unwrap_or("app.sbc");
            compile_file(Path::new(file), Path::new(output))?;
            println!("{}", Path::new(output).display());
            Ok(0)
        }
        "exec" => {
            let file = positional(&args, 1, "exec requires a .sbc file")?;
            exec_bytecode(Path::new(file))?;
            Ok(0)
        }
        "inspect" => inspect(&args),
        "doctor" if args.get(1).map(String::as_str) == Some("native") => {
            doctor_native();
            Ok(0)
        }
        other => Err(DiagnosticList::single(sona_diagnostics::Diagnostic::error(
            "E0001",
            "SONA-NATIVE-CLI-001",
            "cli",
            format!("Unknown native command '{other}'."),
            sona_diagnostics::SourceSpan::unknown(),
            "Use --help to list native preview commands.",
        ))),
    }
}

fn print_help() {
    println!("Sona native {VERSION}");
    println!("Commands:");
    println!("  sona run app.sona --engine native");
    println!("  sona check app.sona --engine native");
    println!("  sona compile app.sona --output app.sbc");
    println!("  sona exec app.sbc");
    println!("  sona inspect tokens|ast|ir|bytecode <file>");
    println!("  sona doctor native");
}

fn run_file(path: &Path) -> SonaResult<()> {
    let source = SourceFile::read(0, path).map_err(io_error)?;
    let program = parse_source(&source)?;
    let bytecode = compile(lower(program)?, Some(source.text.clone()))?;
    let mut vm = Vm::new(Some(path.to_path_buf()));
    vm.execute(&bytecode)?;
    Ok(())
}

fn check_file(path: &Path) -> SonaResult<()> {
    let source = SourceFile::read(0, path).map_err(io_error)?;
    let program = parse_source(&source)?;
    let _bytecode = compile(lower(program)?, Some(source.text.clone()))?;
    Ok(())
}

fn compile_file(path: &Path, output: &Path) -> SonaResult<()> {
    let source = SourceFile::read(0, path).map_err(io_error)?;
    let program = parse_source(&source)?;
    let bytecode = compile(lower(program)?, Some(source.text.clone()))?;
    fs::write(output, encode_source_backed(&bytecode)).map_err(io_error)?;
    Ok(())
}

fn exec_bytecode(path: &Path) -> SonaResult<()> {
    let bytes = fs::read(path).map_err(io_error)?;
    let source_text = decode_source_backed(&bytes, path.display().to_string())?;
    let virtual_source = SourceFile::new(0, path.with_extension("sona"), source_text);
    let program = parse_source(&virtual_source)?;
    let bytecode = compile(lower(program)?, Some(virtual_source.text.clone()))?;
    let mut vm = Vm::new(Some(path.to_path_buf()));
    vm.execute(&bytecode)?;
    Ok(())
}

fn inspect(args: &[String]) -> SonaResult<i32> {
    let mode = positional(args, 1, "inspect requires tokens, ast, ir, or bytecode")?;
    let file = positional(args, 2, "inspect requires a file path")?;
    match mode {
        "tokens" => {
            let source = SourceFile::read(0, file).map_err(io_error)?;
            for token in lex(&source)? {
                println!("{:?}", token.kind);
            }
        }
        "ast" => {
            let source = SourceFile::read(0, file).map_err(io_error)?;
            println!("{:#?}", parse_source(&source)?);
        }
        "ir" => {
            let source = SourceFile::read(0, file).map_err(io_error)?;
            println!("{:#?}", lower(parse_source(&source)?)?);
        }
        "bytecode" => {
            let path = PathBuf::from(file);
            if path.extension().and_then(|item| item.to_str()) == Some("sbc") {
                let bytes = fs::read(path).map_err(io_error)?;
                let source = decode_source_backed(&bytes, file)?;
                let virtual_source = SourceFile::new(0, "<bytecode>", source);
                let bytecode = compile(
                    lower(parse_source(&virtual_source)?)?,
                    Some(virtual_source.text),
                )?;
                println!("version={}", bytecode.version);
                println!("instructions={}", bytecode.instructions.len());
            } else {
                let source = SourceFile::read(0, file).map_err(io_error)?;
                let bytecode = compile(lower(parse_source(&source)?)?, Some(source.text.clone()))?;
                println!("{:#?}", bytecode.instructions);
            }
        }
        other => {
            return Err(DiagnosticList::single(sona_diagnostics::Diagnostic::error(
                "E0001",
                "SONA-NATIVE-CLI-002",
                "cli",
                format!("Unknown inspect target '{other}'."),
                sona_diagnostics::SourceSpan::unknown(),
                "Use tokens, ast, ir, or bytecode.",
            )))
        }
    }
    Ok(0)
}

fn doctor_native() {
    println!("native_binary_version={VERSION}");
    println!("bytecode_version={BYTECODE_VERSION}");
    println!("feature_level=Sona Native Core preview");
    println!("python_required=false");
    println!("python_embedded=false");
    println!("default_capabilities=console:allow,filesystem:deny,network:deny,process:deny,environment:deny");
    println!("modules=smod-preview");
}

fn positional<'a>(args: &'a [String], index: usize, message: &str) -> SonaResult<&'a str> {
    args.get(index).map(String::as_str).ok_or_else(|| {
        DiagnosticList::single(sona_diagnostics::Diagnostic::error(
            "E0001",
            "SONA-NATIVE-CLI-003",
            "cli",
            message,
            sona_diagnostics::SourceSpan::unknown(),
            "Provide the required argument.",
        ))
    })
}

fn option_value<'a>(args: &'a [String], option: &str) -> Option<&'a str> {
    args.windows(2)
        .find(|pair| pair[0] == option)
        .map(|pair| pair[1].as_str())
}

fn require_native_engine(args: &[String]) -> SonaResult<()> {
    match option_value(args, "--engine") {
        Some("native") | None => Ok(()),
        Some("python-compat") | Some("auto") => Err(DiagnosticList::single(sona_diagnostics::Diagnostic::error(
            "E0001",
            "SONA-NATIVE-CLI-004",
            "cli",
            "The native preview binary does not execute through Python compatibility or auto fallback.",
            sona_diagnostics::SourceSpan::unknown(),
            "Use --engine native for this binary.",
        ))),
        Some(other) => Err(DiagnosticList::single(sona_diagnostics::Diagnostic::error(
            "E0001",
            "SONA-NATIVE-CLI-005",
            "cli",
            format!("Unknown engine '{other}'."),
            sona_diagnostics::SourceSpan::unknown(),
            "Use --engine native.",
        ))),
    }
}

fn io_error(err: std::io::Error) -> DiagnosticList {
    DiagnosticList::single(sona_diagnostics::Diagnostic::error(
        "E0601",
        "SONA-NATIVE-IO-001",
        "io",
        err.to_string(),
        sona_diagnostics::SourceSpan::unknown(),
        "Check that the file exists and is readable.",
    ))
}
