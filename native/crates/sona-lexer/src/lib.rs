use sona_diagnostics::{Diagnostic, DiagnosticList, SonaResult, SourceSpan};
use sona_source::SourceFile;

#[derive(Clone, Debug, PartialEq)]
pub enum TokenKind {
    Identifier(String),
    Number(String),
    String(String),
    Keyword(String),
    Symbol(char),
    Operator(String),
    Eof,
}

#[derive(Clone, Debug, PartialEq)]
pub struct Token {
    pub kind: TokenKind,
    pub span: SourceSpan,
}

impl Token {
    fn new(kind: TokenKind, source: &SourceFile, start: usize, end: usize) -> Self {
        let (start_line, start_column) = source.line_column(start);
        let (end_line, end_column) = source.line_column(end.max(start + 1));
        Self {
            kind,
            span: SourceSpan::new(
                source.display_name(),
                start_line,
                start_column,
                end_line,
                end_column,
            ),
        }
    }
}

const KEYWORDS: &[&str] = &[
    "let", "const", "func", "return", "if", "else", "while", "for", "in", "import", "true",
    "false", "nil", "null", "and", "or", "not",
];

pub fn lex(source: &SourceFile) -> SonaResult<Vec<Token>> {
    let chars: Vec<(usize, char)> = source.text.char_indices().collect();
    let mut tokens = Vec::new();
    let mut diagnostics = Vec::new();
    let mut cursor = 0usize;

    while cursor < chars.len() {
        let (byte, ch) = chars[cursor];
        match ch {
            ' ' | '\t' | '\r' | '\n' => {
                cursor += 1;
            }
            '/' if peek(&chars, cursor + 1) == Some('/') => {
                cursor += 2;
                while cursor < chars.len() && chars[cursor].1 != '\n' {
                    cursor += 1;
                }
            }
            '"' => match read_string(source, &chars, cursor) {
                Ok((token, next)) => {
                    tokens.push(token);
                    cursor = next;
                }
                Err(diagnostic) => {
                    diagnostics.push(*diagnostic);
                    break;
                }
            },
            '0'..='9' => {
                let start = cursor;
                cursor += 1;
                while cursor < chars.len() && chars[cursor].1.is_ascii_digit() {
                    cursor += 1;
                }
                if cursor < chars.len() && chars[cursor].1 == '.' {
                    cursor += 1;
                    while cursor < chars.len() && chars[cursor].1.is_ascii_digit() {
                        cursor += 1;
                    }
                }
                let end = byte_end(source, &chars, cursor);
                tokens.push(Token::new(
                    TokenKind::Number(source.text[chars[start].0..end].to_string()),
                    source,
                    chars[start].0,
                    end,
                ));
            }
            'A'..='Z' | 'a'..='z' | '_' => {
                let start = cursor;
                cursor += 1;
                while cursor < chars.len()
                    && (chars[cursor].1.is_ascii_alphanumeric() || chars[cursor].1 == '_')
                {
                    cursor += 1;
                }
                let end = byte_end(source, &chars, cursor);
                let text = &source.text[chars[start].0..end];
                let kind = if KEYWORDS.contains(&text) {
                    TokenKind::Keyword(text.to_string())
                } else {
                    TokenKind::Identifier(text.to_string())
                };
                tokens.push(Token::new(kind, source, chars[start].0, end));
            }
            '(' | ')' | '{' | '}' | '[' | ']' | ',' | ';' | ':' | '.' => {
                tokens.push(Token::new(
                    TokenKind::Symbol(ch),
                    source,
                    byte,
                    byte + ch.len_utf8(),
                ));
                cursor += 1;
            }
            '+' | '-' | '*' | '/' | '%' | '=' | '!' | '<' | '>' => {
                let mut op = ch.to_string();
                if let Some(next) = peek(&chars, cursor + 1) {
                    if matches!(
                        (ch, next),
                        ('*', '*') | ('=', '=') | ('!', '=') | ('<', '=') | ('>', '=')
                    ) {
                        op.push(next);
                        cursor += 1;
                    }
                }
                let end = byte + op.len();
                tokens.push(Token::new(TokenKind::Operator(op), source, byte, end));
                cursor += 1;
            }
            _ => {
                diagnostics.push(Diagnostic::error(
                    "E0001",
                    "SONA-NATIVE-LEX-001",
                    "lexer",
                    format!("Unsupported character '{ch}'."),
                    Token::new(TokenKind::Eof, source, byte, byte + ch.len_utf8()).span,
                    "Use certified Sona syntax.",
                ));
                cursor += 1;
            }
        }
    }

    if !diagnostics.is_empty() {
        return Err(DiagnosticList(diagnostics));
    }
    let eof_offset = source.text.len();
    tokens.push(Token::new(TokenKind::Eof, source, eof_offset, eof_offset));
    Ok(tokens)
}

fn read_string(
    source: &SourceFile,
    chars: &[(usize, char)],
    start_index: usize,
) -> Result<(Token, usize), Box<Diagnostic>> {
    let start_byte = chars[start_index].0;
    let mut cursor = start_index + 1;
    let mut value = String::new();
    while cursor < chars.len() {
        let (byte, ch) = chars[cursor];
        match ch {
            '"' => {
                return Ok((
                    Token::new(TokenKind::String(value), source, start_byte, byte + 1),
                    cursor + 1,
                ));
            }
            '\\' => {
                cursor += 1;
                if cursor >= chars.len() {
                    break;
                }
                value.push(match chars[cursor].1 {
                    'n' => '\n',
                    'r' => '\r',
                    't' => '\t',
                    '"' => '"',
                    '\\' => '\\',
                    other => {
                        return Err(Box::new(Diagnostic::error(
                            "E0005",
                            "SONA-NATIVE-LEX-002",
                            "lexer",
                            format!("Invalid string escape '\\{other}'."),
                            Token::new(
                                TokenKind::Eof,
                                source,
                                chars[cursor].0,
                                chars[cursor].0 + other.len_utf8(),
                            )
                            .span,
                            "Use one of \\\\, \\\", \\n, \\r, or \\t.",
                        )));
                    }
                });
            }
            _ => value.push(ch),
        }
        cursor += 1;
    }
    Err(Box::new(Diagnostic::error(
        "E0003",
        "SONA-NATIVE-LEX-003",
        "lexer",
        "Unterminated string literal.",
        Token::new(TokenKind::Eof, source, start_byte, start_byte + 1).span,
        "Close the string with a double quote.",
    )))
}

fn peek(chars: &[(usize, char)], index: usize) -> Option<char> {
    chars.get(index).map(|(_, ch)| *ch)
}

fn byte_end(source: &SourceFile, chars: &[(usize, char)], cursor: usize) -> usize {
    chars
        .get(cursor)
        .map(|(byte, _)| *byte)
        .unwrap_or_else(|| source.text.len())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn lexes_core_tokens_with_spans() {
        let source = SourceFile::new(0, "test.sona", "let x = 1 + 2;");
        let tokens = lex(&source).unwrap();
        assert!(matches!(tokens[0].kind, TokenKind::Keyword(ref item) if item == "let"));
        assert_eq!(tokens[0].span.start_line, 1);
        assert_eq!(tokens[0].span.start_column, 1);
        assert!(matches!(tokens[1].kind, TokenKind::Identifier(ref item) if item == "x"));
    }
}
