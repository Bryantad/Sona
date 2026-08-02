use sona_ast::{BinaryOp, Expr, Literal, Program, Stmt, UnaryOp};
use sona_diagnostics::{Diagnostic, DiagnosticList, SonaResult, SourceSpan};
use sona_ir::IrProgram;

pub const BYTECODE_VERSION: u16 = 1;
pub const BYTECODE_MAGIC: &[u8; 4] = b"SBC1";
pub const MAX_SOURCE_BYTES: u64 = 16_777_216;

const FIXED_HEADER_BYTES: usize = 8;
const FIELD_FLAGS: u8 = 1;
const FIELD_SOURCE_ENCODING: u8 = 2;
const FIELD_SOURCE_LENGTH: u8 = 3;
const SOURCE_ENCODING_UTF8: u8 = 1;

#[derive(Clone, Debug, PartialEq)]
pub struct BytecodeProgram {
    pub version: u16,
    pub instructions: Vec<Instruction>,
    pub source_text: Option<String>,
}

#[derive(Clone, Debug, PartialEq)]
pub struct FunctionBytecode {
    pub name: String,
    pub params: Vec<String>,
    pub defaults: Vec<Option<Vec<Instruction>>>,
    pub body: Vec<Instruction>,
}

#[derive(Clone, Debug, PartialEq)]
pub enum Constant {
    Null,
    Bool(bool),
    Int(i64),
    Float(f64),
    String(String),
}

#[derive(Clone, Debug, PartialEq)]
pub enum Instruction {
    LoadConst(Constant),
    LoadName(String),
    DeclareName { name: String, is_const: bool },
    StoreName(String),
    DefineFunction(FunctionBytecode),
    Pop,
    Return,
    Jump(usize),
    JumpIfFalse(usize),
    Import(String),
    GetMember(String),
    BuildList(usize),
    BuildMap(Vec<String>),
    Call(usize),
    Add,
    Subtract,
    Multiply,
    Divide,
    Modulo,
    Power,
    Negate,
    Not,
    Equal,
    NotEqual,
    Less,
    LessEqual,
    Greater,
    GreaterEqual,
}

pub fn compile(ir: IrProgram, source_text: Option<String>) -> SonaResult<BytecodeProgram> {
    let mut compiler = Compiler {
        instructions: Vec::new(),
    };
    compiler.compile_program(&ir.program)?;
    compiler
        .instructions
        .push(Instruction::LoadConst(Constant::Null));
    compiler.instructions.push(Instruction::Return);
    Ok(BytecodeProgram {
        version: BYTECODE_VERSION,
        instructions: compiler.instructions,
        source_text,
    })
}

pub fn encode_source_backed(program: &BytecodeProgram) -> Vec<u8> {
    let source = program.source_text.as_deref().unwrap_or("").as_bytes();
    let mut header = Vec::with_capacity(22);
    push_field(&mut header, FIELD_FLAGS, &0u32.to_le_bytes());
    push_field(&mut header, FIELD_SOURCE_ENCODING, &[SOURCE_ENCODING_UTF8]);
    push_field(
        &mut header,
        FIELD_SOURCE_LENGTH,
        &(source.len() as u64).to_le_bytes(),
    );

    let header_length = u16::try_from(header.len()).expect("version 1 header length is bounded");
    let mut encoded = Vec::with_capacity(FIXED_HEADER_BYTES + header.len() + source.len());
    encoded.extend_from_slice(BYTECODE_MAGIC);
    encoded.extend_from_slice(&program.version.to_le_bytes());
    encoded.extend_from_slice(&header_length.to_le_bytes());
    encoded.extend_from_slice(&header);
    encoded.extend_from_slice(source);
    encoded
}

pub fn decode_source_backed(bytes: &[u8], file: impl Into<String>) -> SonaResult<String> {
    let file = file.into();
    if bytes.len() < BYTECODE_MAGIC.len() {
        return Err(container_error(
            &file,
            "SONA-NATIVE-BYTECODE-003",
            "The .sbc header is truncated.",
            "Recompile the source; do not edit the container.",
        ));
    }
    if &bytes[..BYTECODE_MAGIC.len()] != BYTECODE_MAGIC {
        return Err(container_error(
            &file,
            "SONA-NATIVE-BYTECODE-001",
            "Invalid .sbc magic.",
            "Use a .sbc file produced by Sona 0.15.4.",
        ));
    }
    if bytes.len() < FIXED_HEADER_BYTES {
        return Err(container_error(
            &file,
            "SONA-NATIVE-BYTECODE-003",
            "The .sbc header is truncated.",
            "Recompile the source; do not edit the container.",
        ));
    }

    let version = u16::from_le_bytes([bytes[4], bytes[5]]);
    if version != BYTECODE_VERSION {
        return Err(container_error(
            &file,
            "SONA-NATIVE-BYTECODE-004",
            format!("Unsupported .sbc format version {version}."),
            "Recompile the source with Sona 0.15.4.",
        ));
    }
    let header_length = usize::from(u16::from_le_bytes([bytes[6], bytes[7]]));
    let Some(header_end) = FIXED_HEADER_BYTES.checked_add(header_length) else {
        return Err(invalid_numeric(&file, "header length"));
    };
    if header_end > bytes.len() {
        return Err(container_error(
            &file,
            "SONA-NATIVE-BYTECODE-003",
            "The .sbc header is truncated.",
            "Recompile the source; do not edit the container.",
        ));
    }

    let mut cursor = FIXED_HEADER_BYTES;
    let mut last_field = 0u8;
    let mut flags = None;
    let mut encoding = None;
    let mut source_length = None;
    while cursor < header_end {
        if header_end - cursor < 3 {
            return Err(container_error(
                &file,
                "SONA-NATIVE-BYTECODE-003",
                "The .sbc header is truncated.",
                "Recompile the source; do not edit the container.",
            ));
        }
        let field = bytes[cursor];
        let field_length = usize::from(u16::from_le_bytes([bytes[cursor + 1], bytes[cursor + 2]]));
        cursor += 3;
        let Some(field_end) = cursor.checked_add(field_length) else {
            return Err(invalid_numeric(&file, "field length"));
        };
        if field_end > header_end {
            return Err(container_error(
                &file,
                "SONA-NATIVE-BYTECODE-003",
                "The .sbc header is truncated.",
                "Recompile the source; do not edit the container.",
            ));
        }
        if field <= last_field {
            return Err(invalid_header(&file));
        }
        last_field = field;
        let value = &bytes[cursor..field_end];
        match field {
            FIELD_FLAGS => {
                if value.len() != 4 {
                    return Err(invalid_numeric(&file, "flags"));
                }
                let parsed = u32::from_le_bytes(value.try_into().expect("validated field width"));
                if parsed != 0 {
                    return Err(invalid_header(&file));
                }
                flags = Some(parsed);
            }
            FIELD_SOURCE_ENCODING => {
                if value.len() != 1 || value[0] != SOURCE_ENCODING_UTF8 {
                    return Err(invalid_numeric(&file, "source encoding"));
                }
                encoding = Some(value[0]);
            }
            FIELD_SOURCE_LENGTH => {
                if value.len() != 8 {
                    return Err(invalid_numeric(&file, "source length"));
                }
                source_length = Some(u64::from_le_bytes(
                    value.try_into().expect("validated field width"),
                ));
            }
            _ => return Err(invalid_header(&file)),
        }
        cursor = field_end;
    }

    if flags.is_none() {
        return Err(missing_field(&file, "flags"));
    }
    if encoding.is_none() {
        return Err(missing_field(&file, "source encoding"));
    }
    let Some(source_length) = source_length else {
        return Err(missing_field(&file, "source length"));
    };
    if source_length > MAX_SOURCE_BYTES {
        return Err(container_error(
            &file,
            "SONA-NATIVE-BYTECODE-008",
            "The .sbc source payload exceeds the maximum supported size.",
            "Reduce the source to 16777216 bytes or fewer.",
        ));
    }
    let source_length =
        usize::try_from(source_length).map_err(|_| invalid_numeric(&file, "source length"))?;
    let Some(source_end) = header_end.checked_add(source_length) else {
        return Err(invalid_numeric(&file, "source length"));
    };
    if source_end > bytes.len() {
        return Err(container_error(
            &file,
            "SONA-NATIVE-BYTECODE-007",
            "The .sbc source length does not match the declared length.",
            "Recompile the source; the container payload is incomplete.",
        ));
    }
    if source_end < bytes.len() {
        return Err(container_error(
            &file,
            "SONA-NATIVE-BYTECODE-009",
            "The .sbc container has unexpected trailing data.",
            "Recompile the source; trailing bytes are not allowed in format version 1.",
        ));
    }
    std::str::from_utf8(&bytes[header_end..source_end])
        .map(str::to_owned)
        .map_err(|_| {
            container_error(
                &file,
                "SONA-NATIVE-BYTECODE-002",
                "The .sbc source payload is not valid UTF-8.",
                "Recompile the original UTF-8 Sona source.",
            )
        })
}

fn push_field(header: &mut Vec<u8>, field: u8, value: &[u8]) {
    header.push(field);
    header.extend_from_slice(
        &u16::try_from(value.len())
            .expect("version 1 field length is bounded")
            .to_le_bytes(),
    );
    header.extend_from_slice(value);
}

fn container_error(
    file: &str,
    diagnostic_id: &str,
    message: impl Into<String>,
    suggestion: impl Into<String>,
) -> DiagnosticList {
    DiagnosticList::single(Diagnostic::error(
        "E0001",
        diagnostic_id,
        "bytecode",
        message,
        SourceSpan::new(file, 1, 1, 1, 1),
        suggestion,
    ))
}

fn missing_field(file: &str, field: &str) -> DiagnosticList {
    container_error(
        file,
        "SONA-NATIVE-BYTECODE-005",
        format!("The .sbc header is missing required field '{field}'."),
        "Recompile the source; the container header is incomplete.",
    )
}

fn invalid_numeric(file: &str, field: &str) -> DiagnosticList {
    container_error(
        file,
        "SONA-NATIVE-BYTECODE-006",
        format!("The .sbc field '{field}' has an invalid numeric encoding."),
        "Recompile the source; the container header is malformed.",
    )
}

fn invalid_header(file: &str) -> DiagnosticList {
    container_error(
        file,
        "SONA-NATIVE-BYTECODE-010",
        "The .sbc header contains duplicate, unknown, or reserved data.",
        "Recompile the source; format version 1 accepts only its required fields.",
    )
}

struct Compiler {
    instructions: Vec<Instruction>,
}

impl Compiler {
    fn compile_program(&mut self, program: &Program) -> SonaResult<()> {
        for stmt in &program.statements {
            self.compile_stmt(stmt)?;
        }
        Ok(())
    }

    fn compile_block(stmts: &[Stmt]) -> SonaResult<Vec<Instruction>> {
        let mut nested = Compiler {
            instructions: Vec::new(),
        };
        for stmt in stmts {
            nested.compile_stmt(stmt)?;
        }
        nested
            .instructions
            .push(Instruction::LoadConst(Constant::Null));
        nested.instructions.push(Instruction::Return);
        Ok(nested.instructions)
    }

    fn compile_stmt(&mut self, stmt: &Stmt) -> SonaResult<()> {
        match stmt {
            Stmt::Let {
                name,
                value,
                is_const,
                ..
            } => {
                self.compile_expr(value)?;
                self.instructions.push(Instruction::DeclareName {
                    name: name.clone(),
                    is_const: *is_const,
                });
            }
            Stmt::Assign { name, value, .. } => {
                self.compile_expr(value)?;
                self.instructions.push(Instruction::StoreName(name.clone()));
            }
            Stmt::Function {
                name, params, body, ..
            } => {
                let defaults = params
                    .iter()
                    .map(|param| {
                        param.default.as_ref().map(|expr| {
                            let mut nested = Compiler {
                                instructions: Vec::new(),
                            };
                            nested.compile_expr(expr).unwrap_or(());
                            nested.instructions.push(Instruction::Return);
                            nested.instructions
                        })
                    })
                    .collect();
                self.instructions
                    .push(Instruction::DefineFunction(FunctionBytecode {
                        name: name.clone(),
                        params: params.iter().map(|param| param.name.clone()).collect(),
                        defaults,
                        body: Self::compile_block(body)?,
                    }));
            }
            Stmt::Return { value, .. } => {
                if let Some(value) = value {
                    self.compile_expr(value)?;
                } else {
                    self.instructions
                        .push(Instruction::LoadConst(Constant::Null));
                }
                self.instructions.push(Instruction::Return);
            }
            Stmt::If {
                condition,
                then_body,
                else_body,
                ..
            } => {
                self.compile_expr(condition)?;
                let jump_if_false_at = self.instructions.len();
                self.instructions.push(Instruction::JumpIfFalse(usize::MAX));
                for stmt in then_body {
                    self.compile_stmt(stmt)?;
                }
                let jump_end_at = self.instructions.len();
                self.instructions.push(Instruction::Jump(usize::MAX));
                let else_start = self.instructions.len();
                for stmt in else_body {
                    self.compile_stmt(stmt)?;
                }
                let end = self.instructions.len();
                self.instructions[jump_if_false_at] = Instruction::JumpIfFalse(else_start);
                self.instructions[jump_end_at] = Instruction::Jump(end);
            }
            Stmt::While {
                condition, body, ..
            } => {
                let start = self.instructions.len();
                self.compile_expr(condition)?;
                let exit_jump_at = self.instructions.len();
                self.instructions.push(Instruction::JumpIfFalse(usize::MAX));
                for stmt in body {
                    self.compile_stmt(stmt)?;
                }
                self.instructions.push(Instruction::Jump(start));
                let end = self.instructions.len();
                self.instructions[exit_jump_at] = Instruction::JumpIfFalse(end);
            }
            Stmt::Import { module, .. } => {
                self.instructions.push(Instruction::Import(module.clone()))
            }
            Stmt::Print { value, .. } => {
                self.compile_expr(value)?;
                self.instructions
                    .push(Instruction::LoadName("print".to_string()));
                self.instructions.push(Instruction::Call(1));
                self.instructions.push(Instruction::Pop);
            }
            Stmt::Expr { value, .. } => {
                self.compile_expr(value)?;
                self.instructions.push(Instruction::Pop);
            }
        }
        Ok(())
    }

    fn compile_expr(&mut self, expr: &Expr) -> SonaResult<()> {
        match expr {
            Expr::Literal(value, _) => {
                self.instructions.push(Instruction::LoadConst(match value {
                    Literal::Null => Constant::Null,
                    Literal::Bool(value) => Constant::Bool(*value),
                    Literal::Int(value) => Constant::Int(*value),
                    Literal::Float(value) => Constant::Float(*value),
                    Literal::String(value) => Constant::String(value.clone()),
                }))
            }
            Expr::Variable(name, _) => self.instructions.push(Instruction::LoadName(name.clone())),
            Expr::List(items, _) => {
                for item in items {
                    self.compile_expr(item)?;
                }
                self.instructions.push(Instruction::BuildList(items.len()));
            }
            Expr::Map(items, _) => {
                for (_, value) in items {
                    self.compile_expr(value)?;
                }
                self.instructions.push(Instruction::BuildMap(
                    items.iter().map(|(key, _)| key.clone()).collect(),
                ));
            }
            Expr::Unary { op, expr, .. } => {
                self.compile_expr(expr)?;
                self.instructions.push(match op {
                    UnaryOp::Negate => Instruction::Negate,
                    UnaryOp::Not => Instruction::Not,
                });
            }
            Expr::Binary {
                left, op, right, ..
            } => {
                self.compile_expr(left)?;
                self.compile_expr(right)?;
                self.instructions.push(match op {
                    BinaryOp::Add => Instruction::Add,
                    BinaryOp::Subtract => Instruction::Subtract,
                    BinaryOp::Multiply => Instruction::Multiply,
                    BinaryOp::Divide => Instruction::Divide,
                    BinaryOp::Modulo => Instruction::Modulo,
                    BinaryOp::Power => Instruction::Power,
                    BinaryOp::Equal => Instruction::Equal,
                    BinaryOp::NotEqual => Instruction::NotEqual,
                    BinaryOp::Less => Instruction::Less,
                    BinaryOp::LessEqual => Instruction::LessEqual,
                    BinaryOp::Greater => Instruction::Greater,
                    BinaryOp::GreaterEqual => Instruction::GreaterEqual,
                    BinaryOp::And => Instruction::Multiply,
                    BinaryOp::Or => Instruction::Add,
                });
            }
            Expr::Call { callee, args, .. } => {
                self.compile_expr(callee)?;
                for arg in args {
                    self.compile_expr(arg)?;
                }
                self.instructions.push(Instruction::Call(args.len()));
            }
            Expr::Member { object, name, .. } => {
                self.compile_expr(object)?;
                self.instructions.push(Instruction::GetMember(name.clone()));
            }
        }
        Ok(())
    }
}

#[cfg(test)]
mod container_tests {
    use super::*;

    fn program(source: &str) -> BytecodeProgram {
        BytecodeProgram {
            version: BYTECODE_VERSION,
            instructions: Vec::new(),
            source_text: Some(source.to_string()),
        }
    }

    fn diagnostic_id(bytes: &[u8]) -> String {
        decode_source_backed(bytes, "test.sbc")
            .unwrap_err()
            .0
            .first()
            .expect("one diagnostic")
            .diagnostic_id
            .clone()
    }

    fn diagnostic_code(bytes: &[u8]) -> String {
        decode_source_backed(bytes, "test.sbc")
            .unwrap_err()
            .0
            .first()
            .expect("one diagnostic")
            .code
            .clone()
    }

    fn container_with_fields(fields: &[(u8, &[u8])], payload: &[u8]) -> Vec<u8> {
        let mut header = Vec::new();
        for (field, value) in fields {
            push_field(&mut header, *field, value);
        }
        let mut bytes = Vec::new();
        bytes.extend_from_slice(BYTECODE_MAGIC);
        bytes.extend_from_slice(&BYTECODE_VERSION.to_le_bytes());
        bytes.extend_from_slice(&(header.len() as u16).to_le_bytes());
        bytes.extend_from_slice(&header);
        bytes.extend_from_slice(payload);
        bytes
    }

    #[test]
    fn source_backed_container_round_trips_at_length_boundaries() {
        for source in ["", "print(\"hello\");", "π"] {
            let encoded = encode_source_backed(&program(source));
            assert_eq!(decode_source_backed(&encoded, "test.sbc").unwrap(), source);
        }

        let maximum = "x".repeat(MAX_SOURCE_BYTES as usize);
        let encoded = encode_source_backed(&program(&maximum));
        assert_eq!(
            decode_source_backed(&encoded, "test.sbc").unwrap().len(),
            MAX_SOURCE_BYTES as usize
        );
    }

    #[test]
    fn validates_magic_version_and_header_shape() {
        assert_eq!(diagnostic_id(b"SBC"), "SONA-NATIVE-BYTECODE-003");
        let mut invalid_magic = encode_source_backed(&program(""));
        invalid_magic[0] = b'X';
        assert_eq!(diagnostic_id(&invalid_magic), "SONA-NATIVE-BYTECODE-001");
        let mut unsupported_version = encode_source_backed(&program(""));
        unsupported_version[4..6].copy_from_slice(&2u16.to_le_bytes());
        assert_eq!(
            diagnostic_id(&unsupported_version),
            "SONA-NATIVE-BYTECODE-004"
        );
        let mut truncated_header = encode_source_backed(&program(""));
        truncated_header.truncate(12);
        assert_eq!(diagnostic_id(&truncated_header), "SONA-NATIVE-BYTECODE-003");
    }

    #[test]
    fn validates_required_and_numeric_fields() {
        let flags = 0u32.to_le_bytes();
        let encoding = [SOURCE_ENCODING_UTF8];
        let missing_length = container_with_fields(
            &[
                (FIELD_FLAGS, flags.as_slice()),
                (FIELD_SOURCE_ENCODING, encoding.as_slice()),
            ],
            b"",
        );
        assert_eq!(diagnostic_id(&missing_length), "SONA-NATIVE-BYTECODE-005");
        let missing_flags = container_with_fields(
            &[
                (FIELD_SOURCE_ENCODING, encoding.as_slice()),
                (FIELD_SOURCE_LENGTH, 0u64.to_le_bytes().as_slice()),
            ],
            b"",
        );
        assert_eq!(diagnostic_id(&missing_flags), "SONA-NATIVE-BYTECODE-005");
        let missing_encoding = container_with_fields(
            &[
                (FIELD_FLAGS, flags.as_slice()),
                (FIELD_SOURCE_LENGTH, 0u64.to_le_bytes().as_slice()),
            ],
            b"",
        );
        assert_eq!(diagnostic_id(&missing_encoding), "SONA-NATIVE-BYTECODE-005");

        let invalid_flags = container_with_fields(
            &[
                (FIELD_FLAGS, &[0, 0, 0]),
                (FIELD_SOURCE_ENCODING, encoding.as_slice()),
                (FIELD_SOURCE_LENGTH, 0u64.to_le_bytes().as_slice()),
            ],
            b"",
        );
        assert_eq!(diagnostic_id(&invalid_flags), "SONA-NATIVE-BYTECODE-006");
        let invalid_encoding = container_with_fields(
            &[
                (FIELD_FLAGS, flags.as_slice()),
                (FIELD_SOURCE_ENCODING, &[2]),
                (FIELD_SOURCE_LENGTH, 0u64.to_le_bytes().as_slice()),
            ],
            b"",
        );
        assert_eq!(diagnostic_id(&invalid_encoding), "SONA-NATIVE-BYTECODE-006");
        let invalid_length_width = container_with_fields(
            &[
                (FIELD_FLAGS, flags.as_slice()),
                (FIELD_SOURCE_ENCODING, encoding.as_slice()),
                (FIELD_SOURCE_LENGTH, &[0; 7]),
            ],
            b"",
        );
        assert_eq!(
            diagnostic_id(&invalid_length_width),
            "SONA-NATIVE-BYTECODE-006"
        );

        let duplicate_flags = container_with_fields(
            &[
                (FIELD_FLAGS, flags.as_slice()),
                (FIELD_FLAGS, flags.as_slice()),
                (FIELD_SOURCE_ENCODING, encoding.as_slice()),
                (FIELD_SOURCE_LENGTH, 0u64.to_le_bytes().as_slice()),
            ],
            b"",
        );
        assert_eq!(diagnostic_id(&duplicate_flags), "SONA-NATIVE-BYTECODE-010");

        let nonzero_flags = container_with_fields(
            &[
                (FIELD_FLAGS, 1u32.to_le_bytes().as_slice()),
                (FIELD_SOURCE_ENCODING, encoding.as_slice()),
                (FIELD_SOURCE_LENGTH, 0u64.to_le_bytes().as_slice()),
            ],
            b"",
        );
        assert_eq!(diagnostic_id(&nonzero_flags), "SONA-NATIVE-BYTECODE-010");
        let unknown_field = container_with_fields(
            &[
                (FIELD_FLAGS, flags.as_slice()),
                (FIELD_SOURCE_ENCODING, encoding.as_slice()),
                (FIELD_SOURCE_LENGTH, 0u64.to_le_bytes().as_slice()),
                (4, &[]),
            ],
            b"",
        );
        assert_eq!(diagnostic_id(&unknown_field), "SONA-NATIVE-BYTECODE-010");
        let reserved_field = container_with_fields(
            &[
                (0, &[]),
                (FIELD_FLAGS, flags.as_slice()),
                (FIELD_SOURCE_ENCODING, encoding.as_slice()),
                (FIELD_SOURCE_LENGTH, 0u64.to_le_bytes().as_slice()),
            ],
            b"",
        );
        assert_eq!(diagnostic_id(&reserved_field), "SONA-NATIVE-BYTECODE-010");
        let out_of_order = container_with_fields(
            &[
                (FIELD_SOURCE_ENCODING, encoding.as_slice()),
                (FIELD_FLAGS, flags.as_slice()),
                (FIELD_SOURCE_LENGTH, 0u64.to_le_bytes().as_slice()),
            ],
            b"",
        );
        assert_eq!(diagnostic_id(&out_of_order), "SONA-NATIVE-BYTECODE-010");

        for malformed in [
            b"SBC1\x01\x00\x01\x00\x01".as_slice(),
            b"SBC1\x01\x00\x03\x00\x01\x04".as_slice(),
            b"SBC1\x01\x00\x07\x00\x01\x04\x00\x00\x00".as_slice(),
        ] {
            assert_eq!(diagnostic_id(malformed), "SONA-NATIVE-BYTECODE-003");
        }
    }

    #[test]
    fn validates_payload_length_encoding_and_trailing_data() {
        let mut mismatch = encode_source_backed(&program("x"));
        mismatch[22..30].copy_from_slice(&2u64.to_le_bytes());
        assert_eq!(diagnostic_id(&mismatch), "SONA-NATIVE-BYTECODE-007");

        let mut invalid_utf8 = encode_source_backed(&program("x"));
        *invalid_utf8.last_mut().expect("payload") = 0xff;
        assert_eq!(diagnostic_id(&invalid_utf8), "SONA-NATIVE-BYTECODE-002");

        let mut oversized = encode_source_backed(&program(""));
        oversized[22..30].copy_from_slice(&(MAX_SOURCE_BYTES + 1).to_le_bytes());
        assert_eq!(diagnostic_id(&oversized), "SONA-NATIVE-BYTECODE-008");
        oversized[22..30].copy_from_slice(&u64::MAX.to_le_bytes());
        assert_eq!(diagnostic_id(&oversized), "SONA-NATIVE-BYTECODE-008");

        let mut trailing = encode_source_backed(&program("x"));
        trailing.push(0);
        assert_eq!(diagnostic_id(&trailing), "SONA-NATIVE-BYTECODE-009");
    }

    #[test]
    fn malformed_containers_never_panic() {
        let valid = encode_source_backed(&program("print(1);"));
        for length in 0..valid.len() {
            assert!(std::panic::catch_unwind(|| {
                let _ = decode_source_backed(&valid[..length], "test.sbc");
            })
            .is_ok());
        }
        for index in 0..valid.len() {
            let mut mutated = valid.clone();
            mutated[index] ^= 0xff;
            assert!(std::panic::catch_unwind(|| {
                let _ = decode_source_backed(&mutated, "test.sbc");
            })
            .is_ok());
        }

        let mut state = 0xC0FFEEu64;
        for length in 0..=256usize {
            let mut arbitrary = vec![0u8; length];
            for byte in &mut arbitrary {
                state = state
                    .wrapping_mul(6_364_136_223_846_793_005)
                    .wrapping_add(1);
                *byte = (state >> 32) as u8;
            }
            assert!(std::panic::catch_unwind(|| {
                let _ = decode_source_backed(&arbitrary, "fuzz.sbc");
            })
            .is_ok());
        }
    }

    #[test]
    fn every_container_failure_uses_e0001() {
        for bytes in [
            b"bad".as_slice(),
            b"SBC1\x02\x00\x00\x00".as_slice(),
            b"SBC1\x01\x00\x00\x00".as_slice(),
        ] {
            assert_eq!(diagnostic_code(bytes), "E0001");
        }
    }
}
