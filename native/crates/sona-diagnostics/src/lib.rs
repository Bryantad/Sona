use std::fmt;

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct SourceSpan {
    pub file: String,
    pub start_line: usize,
    pub start_column: usize,
    pub end_line: usize,
    pub end_column: usize,
}

impl SourceSpan {
    pub fn new(
        file: impl Into<String>,
        start_line: usize,
        start_column: usize,
        end_line: usize,
        end_column: usize,
    ) -> Self {
        Self {
            file: file.into(),
            start_line: start_line.max(1),
            start_column: start_column.max(1),
            end_line: end_line.max(1),
            end_column: end_column.max(1),
        }
    }

    pub fn unknown() -> Self {
        Self::new("<unknown>", 1, 1, 1, 1)
    }
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Severity {
    Error,
    Warning,
    Info,
}

impl Severity {
    pub fn as_str(&self) -> &'static str {
        match self {
            Severity::Error => "error",
            Severity::Warning => "warning",
            Severity::Info => "info",
        }
    }
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Diagnostic {
    pub schema: u8,
    pub code: String,
    pub diagnostic_id: String,
    pub severity: Severity,
    pub category: String,
    pub message: String,
    pub plain_explanation: String,
    pub span: SourceSpan,
    pub suggestions: Vec<String>,
}

impl Diagnostic {
    pub fn error(
        code: impl Into<String>,
        diagnostic_id: impl Into<String>,
        category: impl Into<String>,
        message: impl Into<String>,
        span: SourceSpan,
        suggestion: impl Into<String>,
    ) -> Self {
        let message = message.into();
        Self {
            schema: 1,
            code: code.into(),
            diagnostic_id: diagnostic_id.into(),
            severity: Severity::Error,
            category: category.into(),
            plain_explanation: message.clone(),
            message,
            span,
            suggestions: vec![suggestion.into()],
        }
    }

    pub fn to_json_line(&self) -> String {
        format!(
            "{{\"schema\":{},\"code\":\"{}\",\"diagnostic_id\":\"{}\",\"severity\":\"{}\",\"category\":\"{}\",\"message\":\"{}\",\"file\":\"{}\",\"span\":{{\"start_line\":{},\"start_column\":{},\"end_line\":{},\"end_column\":{}}},\"suggestions\":[{}]}}",
            self.schema,
            escape(&self.code),
            escape(&self.diagnostic_id),
            self.severity.as_str(),
            escape(&self.category),
            escape(&self.message),
            escape(&self.span.file),
            self.span.start_line,
            self.span.start_column,
            self.span.end_line,
            self.span.end_column,
            self.suggestions
                .iter()
                .map(|item| format!("\"{}\"", escape(item)))
                .collect::<Vec<_>>()
                .join(",")
        )
    }
}

impl fmt::Display for Diagnostic {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "{}[{}] {}: {}\n  --> {}:{}:{}",
            self.severity.as_str(),
            self.code,
            self.diagnostic_id,
            self.message,
            self.span.file,
            self.span.start_line,
            self.span.start_column
        )?;
        if let Some(first) = self.suggestions.first() {
            write!(f, "\n  hint: {}", first)?;
        }
        Ok(())
    }
}

#[derive(Clone, Debug)]
pub struct DiagnosticList(pub Vec<Diagnostic>);

impl DiagnosticList {
    pub fn single(diagnostic: Diagnostic) -> Self {
        Self(vec![diagnostic])
    }
}

impl fmt::Display for DiagnosticList {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        for (index, diagnostic) in self.0.iter().enumerate() {
            if index > 0 {
                writeln!(f)?;
            }
            write!(f, "{diagnostic}")?;
        }
        Ok(())
    }
}

impl std::error::Error for DiagnosticList {}

pub type SonaResult<T> = Result<T, DiagnosticList>;

fn escape(value: &str) -> String {
    value
        .replace('\\', "\\\\")
        .replace('"', "\\\"")
        .replace('\n', "\\n")
        .replace('\r', "\\r")
        .replace('\t', "\\t")
}
