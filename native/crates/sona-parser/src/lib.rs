use sona_ast::{BinaryOp, Expr, Literal, Param, Program, Stmt, UnaryOp};
use sona_diagnostics::{Diagnostic, DiagnosticList, SonaResult, SourceSpan};
use sona_lexer::{lex, Token, TokenKind};
use sona_source::SourceFile;

pub fn parse_source(source: &SourceFile) -> SonaResult<Program> {
    let tokens = lex(source)?;
    Parser::new(tokens).parse_program()
}

struct Parser {
    tokens: Vec<Token>,
    cursor: usize,
}

impl Parser {
    fn new(tokens: Vec<Token>) -> Self {
        Self { tokens, cursor: 0 }
    }

    fn parse_program(&mut self) -> SonaResult<Program> {
        let span = self.peek().span.clone();
        let mut statements = Vec::new();
        while !self.is_eof() {
            if self.consume_symbol(';') {
                continue;
            }
            statements.push(self.parse_statement()?);
            self.consume_symbol(';');
        }
        Ok(Program { statements, span })
    }

    fn parse_statement(&mut self) -> SonaResult<Stmt> {
        if self.matches_keyword("let") || self.matches_keyword("const") {
            return self.parse_declaration();
        }
        if self.matches_keyword("func") {
            return self.parse_function();
        }
        if self.matches_keyword("return") {
            return self.parse_return();
        }
        if self.matches_keyword("if") {
            return self.parse_if();
        }
        if self.matches_keyword("while") {
            return self.parse_while();
        }
        if self.matches_keyword("import") {
            return self.parse_import();
        }
        if self.matches_keyword("for") {
            return Err(self.error_here(
                "E0001",
                "SONA-NATIVE-PARSE-004",
                "Native preview does not yet support for-loops.",
                "Use while loops in the Native Core preview.",
            ));
        }
        if self.matches_identifier("use") {
            return Err(self.error_here(
                "E0001",
                "SONA-NATIVE-PARSE-002",
                "'use' module syntax is not supported.",
                "Use canonical module syntax: import module;",
            ));
        }
        if self.is_legacy_fn_declaration() {
            return Err(self.error_here(
                "E0001",
                "SONA-PARSE-001",
                "The 'fn' keyword is not supported in Sona.",
                "Use 'func' to declare a function.",
            ));
        }
        if let TokenKind::Identifier(name) = self.peek().kind.clone() {
            if self.peek_n_is_operator(1, "=") {
                let span = self.advance().span.clone();
                self.expect_operator("=")?;
                let value = self.parse_expression()?;
                return Ok(Stmt::Assign { name, value, span });
            }
        }
        let expr = self.parse_expression()?;
        let span = expr.span().clone();
        Ok(Stmt::Expr { value: expr, span })
    }

    fn parse_declaration(&mut self) -> SonaResult<Stmt> {
        let is_const = self.matches_keyword("const");
        let span = self.advance().span.clone();
        let name = self.expect_identifier("Expected a binding name after let/const.")?;
        self.expect_operator("=")?;
        let value = self.parse_expression()?;
        Ok(Stmt::Let {
            name,
            value,
            is_const,
            span,
        })
    }

    fn parse_function(&mut self) -> SonaResult<Stmt> {
        let span = self.advance().span.clone();
        let name = self.expect_identifier("Expected function name after func.")?;
        self.expect_symbol('(')?;
        let mut params = Vec::new();
        if !self.check_symbol(')') {
            loop {
                let param_span = self.peek().span.clone();
                let name = self.expect_identifier("Expected parameter name.")?;
                let default = if self.consume_operator("=") {
                    Some(self.parse_expression()?)
                } else {
                    None
                };
                params.push(Param {
                    name,
                    default,
                    span: param_span,
                });
                if !self.consume_symbol(',') {
                    break;
                }
            }
        }
        self.expect_symbol(')')?;
        let body = self.parse_block()?;
        Ok(Stmt::Function {
            name,
            params,
            body,
            span,
        })
    }

    fn parse_return(&mut self) -> SonaResult<Stmt> {
        let span = self.advance().span.clone();
        let value = if self.check_symbol(';') || self.check_symbol('}') || self.is_eof() {
            None
        } else {
            Some(self.parse_expression()?)
        };
        Ok(Stmt::Return { value, span })
    }

    fn parse_if(&mut self) -> SonaResult<Stmt> {
        let span = self.advance().span.clone();
        let condition = self.parse_expression()?;
        let then_body = self.parse_block()?;
        let else_body = if self.consume_keyword("else") {
            self.parse_block()?
        } else {
            Vec::new()
        };
        Ok(Stmt::If {
            condition,
            then_body,
            else_body,
            span,
        })
    }

    fn parse_while(&mut self) -> SonaResult<Stmt> {
        let span = self.advance().span.clone();
        let condition = self.parse_expression()?;
        let body = self.parse_block()?;
        Ok(Stmt::While {
            condition,
            body,
            span,
        })
    }

    fn parse_import(&mut self) -> SonaResult<Stmt> {
        let span = self.advance().span.clone();
        let mut module = self.expect_identifier("Expected module name after import.")?;
        while self.consume_symbol('.') {
            module.push('.');
            module.push_str(&self.expect_identifier("Expected module segment after '.'.")?);
        }
        Ok(Stmt::Import { module, span })
    }

    fn parse_block(&mut self) -> SonaResult<Vec<Stmt>> {
        self.expect_symbol('{')?;
        let mut statements = Vec::new();
        while !self.check_symbol('}') && !self.is_eof() {
            if self.consume_symbol(';') {
                continue;
            }
            statements.push(self.parse_statement()?);
            self.consume_symbol(';');
        }
        self.expect_symbol('}')?;
        Ok(statements)
    }

    fn parse_expression(&mut self) -> SonaResult<Expr> {
        self.parse_or()
    }

    fn parse_or(&mut self) -> SonaResult<Expr> {
        let mut expr = self.parse_and()?;
        while self.consume_keyword("or") {
            let op_span = expr.span().clone();
            let right = self.parse_and()?;
            expr = Expr::Binary {
                left: Box::new(expr),
                op: BinaryOp::Or,
                right: Box::new(right),
                span: op_span,
            };
        }
        Ok(expr)
    }

    fn parse_and(&mut self) -> SonaResult<Expr> {
        let mut expr = self.parse_equality()?;
        while self.consume_keyword("and") {
            let op_span = expr.span().clone();
            let right = self.parse_equality()?;
            expr = Expr::Binary {
                left: Box::new(expr),
                op: BinaryOp::And,
                right: Box::new(right),
                span: op_span,
            };
        }
        Ok(expr)
    }

    fn parse_equality(&mut self) -> SonaResult<Expr> {
        let mut expr = self.parse_comparison()?;
        while self.matches_operator("==") || self.matches_operator("!=") {
            let op = if self.consume_operator("==") {
                BinaryOp::Equal
            } else {
                self.expect_operator("!=")?;
                BinaryOp::NotEqual
            };
            let span = expr.span().clone();
            let right = self.parse_comparison()?;
            expr = Expr::Binary {
                left: Box::new(expr),
                op,
                right: Box::new(right),
                span,
            };
        }
        Ok(expr)
    }

    fn parse_comparison(&mut self) -> SonaResult<Expr> {
        let mut expr = self.parse_term()?;
        while self.matches_operator("<")
            || self.matches_operator("<=")
            || self.matches_operator(">")
            || self.matches_operator(">=")
        {
            let op = match self.advance().kind.clone() {
                TokenKind::Operator(item) if item == "<" => BinaryOp::Less,
                TokenKind::Operator(item) if item == "<=" => BinaryOp::LessEqual,
                TokenKind::Operator(item) if item == ">" => BinaryOp::Greater,
                TokenKind::Operator(item) if item == ">=" => BinaryOp::GreaterEqual,
                _ => unreachable!(),
            };
            let span = expr.span().clone();
            let right = self.parse_term()?;
            expr = Expr::Binary {
                left: Box::new(expr),
                op,
                right: Box::new(right),
                span,
            };
        }
        Ok(expr)
    }

    fn parse_term(&mut self) -> SonaResult<Expr> {
        let mut expr = self.parse_factor()?;
        while self.matches_operator("+") || self.matches_operator("-") {
            let op = if self.consume_operator("+") {
                BinaryOp::Add
            } else {
                self.expect_operator("-")?;
                BinaryOp::Subtract
            };
            let span = expr.span().clone();
            let right = self.parse_factor()?;
            expr = Expr::Binary {
                left: Box::new(expr),
                op,
                right: Box::new(right),
                span,
            };
        }
        Ok(expr)
    }

    fn parse_factor(&mut self) -> SonaResult<Expr> {
        let mut expr = self.parse_power()?;
        while self.matches_operator("*") || self.matches_operator("/") || self.matches_operator("%")
        {
            let op = match self.advance().kind.clone() {
                TokenKind::Operator(item) if item == "*" => BinaryOp::Multiply,
                TokenKind::Operator(item) if item == "/" => BinaryOp::Divide,
                TokenKind::Operator(item) if item == "%" => BinaryOp::Modulo,
                _ => unreachable!(),
            };
            let span = expr.span().clone();
            let right = self.parse_power()?;
            expr = Expr::Binary {
                left: Box::new(expr),
                op,
                right: Box::new(right),
                span,
            };
        }
        Ok(expr)
    }

    fn parse_power(&mut self) -> SonaResult<Expr> {
        let expr = self.parse_unary()?;
        if self.consume_operator("**") {
            let span = expr.span().clone();
            let right = self.parse_power()?;
            return Ok(Expr::Binary {
                left: Box::new(expr),
                op: BinaryOp::Power,
                right: Box::new(right),
                span,
            });
        }
        Ok(expr)
    }

    fn parse_unary(&mut self) -> SonaResult<Expr> {
        if self.consume_operator("-") {
            let span = self.previous().span.clone();
            let expr = self.parse_unary()?;
            return Ok(Expr::Unary {
                op: UnaryOp::Negate,
                expr: Box::new(expr),
                span,
            });
        }
        if self.consume_keyword("not") || self.consume_operator("!") {
            let span = self.previous().span.clone();
            let expr = self.parse_unary()?;
            return Ok(Expr::Unary {
                op: UnaryOp::Not,
                expr: Box::new(expr),
                span,
            });
        }
        self.parse_postfix()
    }

    fn parse_postfix(&mut self) -> SonaResult<Expr> {
        let mut expr = self.parse_primary()?;
        loop {
            if self.consume_symbol('(') {
                let mut args = Vec::new();
                if !self.check_symbol(')') {
                    loop {
                        args.push(self.parse_expression()?);
                        if !self.consume_symbol(',') {
                            break;
                        }
                    }
                }
                let close = self.expect_symbol(')')?;
                expr = Expr::Call {
                    callee: Box::new(expr),
                    args,
                    span: close,
                };
            } else if self.consume_symbol('.') {
                let span = self.previous().span.clone();
                let name = self.expect_identifier("Expected member name after '.'.")?;
                expr = Expr::Member {
                    object: Box::new(expr),
                    name,
                    span,
                };
            } else {
                break;
            }
        }
        Ok(expr)
    }

    fn parse_primary(&mut self) -> SonaResult<Expr> {
        let token = self.advance().clone();
        match token.kind {
            TokenKind::Number(text) => {
                if text.contains('.') {
                    Ok(Expr::Literal(
                        Literal::Float(text.parse().unwrap_or(0.0)),
                        token.span,
                    ))
                } else {
                    Ok(Expr::Literal(
                        Literal::Int(text.parse().unwrap_or(0)),
                        token.span,
                    ))
                }
            }
            TokenKind::String(value) => Ok(Expr::Literal(Literal::String(value), token.span)),
            TokenKind::Identifier(name) => Ok(Expr::Variable(name, token.span)),
            TokenKind::Keyword(value) if value == "true" => {
                Ok(Expr::Literal(Literal::Bool(true), token.span))
            }
            TokenKind::Keyword(value) if value == "false" => {
                Ok(Expr::Literal(Literal::Bool(false), token.span))
            }
            TokenKind::Keyword(value) if value == "nil" || value == "null" => {
                Ok(Expr::Literal(Literal::Null, token.span))
            }
            TokenKind::Symbol('(') => {
                let expr = self.parse_expression()?;
                self.expect_symbol(')')?;
                Ok(expr)
            }
            TokenKind::Symbol('[') => {
                let mut items = Vec::new();
                if !self.check_symbol(']') {
                    loop {
                        items.push(self.parse_expression()?);
                        if !self.consume_symbol(',') {
                            break;
                        }
                    }
                }
                self.expect_symbol(']')?;
                Ok(Expr::List(items, token.span))
            }
            TokenKind::Symbol('{') => {
                let mut items = Vec::new();
                if !self.check_symbol('}') {
                    loop {
                        let key = match self.advance().kind.clone() {
                            TokenKind::Identifier(name) | TokenKind::String(name) => name,
                            _ => {
                                return Err(self.error_at(
                                    &token.span,
                                    "E0001",
                                    "SONA-NATIVE-PARSE-005",
                                    "Expected map key.",
                                    "Use string or identifier keys in map literals.",
                                ))
                            }
                        };
                        self.expect_symbol(':')?;
                        let value = self.parse_expression()?;
                        items.push((key, value));
                        if !self.consume_symbol(',') {
                            break;
                        }
                    }
                }
                self.expect_symbol('}')?;
                Ok(Expr::Map(items, token.span))
            }
            _ => Err(self.error_at(
                &token.span,
                "E0001",
                "SONA-NATIVE-PARSE-001",
                "Expected an expression.",
                "Complete the expression using certified Sona syntax.",
            )),
        }
    }

    fn expect_identifier(&mut self, message: &str) -> SonaResult<String> {
        match self.advance().kind.clone() {
            TokenKind::Identifier(name) => Ok(name),
            _ => Err(self.error_here(
                "E0001",
                "SONA-NATIVE-PARSE-001",
                message,
                "Use an identifier here.",
            )),
        }
    }

    fn expect_symbol(&mut self, symbol: char) -> SonaResult<SourceSpan> {
        if self.consume_symbol(symbol) {
            Ok(self.previous().span.clone())
        } else {
            Err(self.error_here(
                "E0001",
                "SONA-NATIVE-PARSE-001",
                format!("Expected '{symbol}'."),
                "Check delimiters and statement boundaries.",
            ))
        }
    }

    fn expect_operator(&mut self, op: &str) -> SonaResult<()> {
        if self.consume_operator(op) {
            Ok(())
        } else {
            Err(self.error_here(
                "E0001",
                "SONA-NATIVE-PARSE-001",
                format!("Expected operator '{op}'."),
                "Check the expression syntax.",
            ))
        }
    }

    fn consume_symbol(&mut self, symbol: char) -> bool {
        if self.check_symbol(symbol) {
            self.cursor += 1;
            true
        } else {
            false
        }
    }

    fn consume_keyword(&mut self, keyword: &str) -> bool {
        if self.matches_keyword(keyword) {
            self.cursor += 1;
            true
        } else {
            false
        }
    }

    fn consume_operator(&mut self, op: &str) -> bool {
        if self.matches_operator(op) {
            self.cursor += 1;
            true
        } else {
            false
        }
    }

    fn matches_keyword(&self, keyword: &str) -> bool {
        matches!(&self.peek().kind, TokenKind::Keyword(item) if item == keyword)
    }

    fn matches_identifier(&self, name: &str) -> bool {
        matches!(&self.peek().kind, TokenKind::Identifier(item) if item == name)
    }

    fn matches_operator(&self, op: &str) -> bool {
        matches!(&self.peek().kind, TokenKind::Operator(item) if item == op)
    }

    fn check_symbol(&self, symbol: char) -> bool {
        matches!(self.peek().kind, TokenKind::Symbol(item) if item == symbol)
    }

    fn peek_n_is_operator(&self, offset: usize, op: &str) -> bool {
        matches!(self.tokens.get(self.cursor + offset).map(|t| &t.kind), Some(TokenKind::Operator(item)) if item == op)
    }

    fn is_legacy_fn_declaration(&self) -> bool {
        matches!(&self.peek().kind, TokenKind::Identifier(item) if item == "fn")
            && matches!(
                self.tokens.get(self.cursor + 1).map(|token| &token.kind),
                Some(TokenKind::Identifier(_))
            )
            && matches!(
                self.tokens.get(self.cursor + 2).map(|token| &token.kind),
                Some(TokenKind::Symbol('('))
            )
    }

    fn is_eof(&self) -> bool {
        matches!(self.peek().kind, TokenKind::Eof)
    }

    fn peek(&self) -> &Token {
        self.tokens
            .get(self.cursor)
            .unwrap_or_else(|| self.tokens.last().expect("parser must have eof token"))
    }

    fn previous(&self) -> &Token {
        self.tokens
            .get(self.cursor.saturating_sub(1))
            .unwrap_or_else(|| self.tokens.first().expect("parser must have tokens"))
    }

    fn advance(&mut self) -> &Token {
        if !self.is_eof() {
            self.cursor += 1;
        }
        self.previous()
    }

    fn error_here(
        &self,
        code: impl Into<String>,
        diagnostic_id: impl Into<String>,
        message: impl Into<String>,
        suggestion: impl Into<String>,
    ) -> DiagnosticList {
        self.error_at(&self.peek().span, code, diagnostic_id, message, suggestion)
    }

    fn error_at(
        &self,
        span: &SourceSpan,
        code: impl Into<String>,
        diagnostic_id: impl Into<String>,
        message: impl Into<String>,
        suggestion: impl Into<String>,
    ) -> DiagnosticList {
        DiagnosticList::single(Diagnostic::error(
            code,
            diagnostic_id,
            "parser",
            message,
            span.clone(),
            suggestion,
        ))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parses_function_and_call() {
        let source = SourceFile::new(
            0,
            "test.sona",
            "func add(a,b){ return a+b; }; print(add(2,3));",
        );
        let program = parse_source(&source).unwrap();
        assert_eq!(program.statements.len(), 2);
    }

    #[test]
    fn rejects_legacy_use() {
        let source = SourceFile::new(0, "test.sona", "use math;");
        let err = parse_source(&source).unwrap_err();
        assert_eq!(err.0[0].diagnostic_id, "SONA-NATIVE-PARSE-002");
    }

    #[test]
    fn reports_legacy_fn_at_keyword_and_allows_fn_identifiers() {
        let source = SourceFile::new(0, "test.sona", "fn add(a) { return a; }");
        let err = parse_source(&source).unwrap_err();
        let diagnostic = &err.0[0];
        assert_eq!(diagnostic.diagnostic_id, "SONA-PARSE-001");
        assert_eq!(diagnostic.code, "E0001");
        assert_eq!(
            diagnostic.message,
            "The 'fn' keyword is not supported in Sona."
        );
        assert_eq!(
            diagnostic.suggestions,
            vec!["Use 'func' to declare a function."]
        );
        assert_eq!(diagnostic.span.start_line, 1);
        assert_eq!(diagnostic.span.start_column, 1);

        let identifier = SourceFile::new(0, "test.sona", "let fn = \"value\"; print(fn);");
        assert!(parse_source(&identifier).is_ok());
        let property = SourceFile::new(0, "test.sona", "print(module.fn);");
        assert!(parse_source(&property).is_ok());
        let canonical = SourceFile::new(0, "test.sona", "func add(a) { return a; }");
        assert!(parse_source(&canonical).is_ok());
    }
}
