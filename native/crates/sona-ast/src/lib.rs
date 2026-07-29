use sona_diagnostics::SourceSpan;

#[derive(Clone, Debug, PartialEq)]
pub struct Program {
    pub statements: Vec<Stmt>,
    pub span: SourceSpan,
}

#[derive(Clone, Debug, PartialEq)]
pub struct Param {
    pub name: String,
    pub default: Option<Expr>,
    pub span: SourceSpan,
}

#[derive(Clone, Debug, PartialEq)]
pub enum Stmt {
    Let {
        name: String,
        value: Expr,
        is_const: bool,
        span: SourceSpan,
    },
    Assign {
        name: String,
        value: Expr,
        span: SourceSpan,
    },
    Function {
        name: String,
        params: Vec<Param>,
        body: Vec<Stmt>,
        span: SourceSpan,
    },
    Return {
        value: Option<Expr>,
        span: SourceSpan,
    },
    If {
        condition: Expr,
        then_body: Vec<Stmt>,
        else_body: Vec<Stmt>,
        span: SourceSpan,
    },
    While {
        condition: Expr,
        body: Vec<Stmt>,
        span: SourceSpan,
    },
    Import {
        module: String,
        span: SourceSpan,
    },
    Print {
        value: Expr,
        span: SourceSpan,
    },
    Expr {
        value: Expr,
        span: SourceSpan,
    },
}

impl Stmt {
    pub fn span(&self) -> &SourceSpan {
        match self {
            Stmt::Let { span, .. }
            | Stmt::Assign { span, .. }
            | Stmt::Function { span, .. }
            | Stmt::Return { span, .. }
            | Stmt::If { span, .. }
            | Stmt::While { span, .. }
            | Stmt::Import { span, .. }
            | Stmt::Print { span, .. }
            | Stmt::Expr { span, .. } => span,
        }
    }
}

#[derive(Clone, Debug, PartialEq)]
pub enum Expr {
    Literal(Literal, SourceSpan),
    Variable(String, SourceSpan),
    List(Vec<Expr>, SourceSpan),
    Map(Vec<(String, Expr)>, SourceSpan),
    Unary {
        op: UnaryOp,
        expr: Box<Expr>,
        span: SourceSpan,
    },
    Binary {
        left: Box<Expr>,
        op: BinaryOp,
        right: Box<Expr>,
        span: SourceSpan,
    },
    Call {
        callee: Box<Expr>,
        args: Vec<Expr>,
        span: SourceSpan,
    },
    Member {
        object: Box<Expr>,
        name: String,
        span: SourceSpan,
    },
}

impl Expr {
    pub fn span(&self) -> &SourceSpan {
        match self {
            Expr::Literal(_, span)
            | Expr::Variable(_, span)
            | Expr::List(_, span)
            | Expr::Map(_, span)
            | Expr::Unary { span, .. }
            | Expr::Binary { span, .. }
            | Expr::Call { span, .. }
            | Expr::Member { span, .. } => span,
        }
    }
}

#[derive(Clone, Debug, PartialEq)]
pub enum Literal {
    Null,
    Bool(bool),
    Int(i64),
    Float(f64),
    String(String),
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum UnaryOp {
    Negate,
    Not,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum BinaryOp {
    Add,
    Subtract,
    Multiply,
    Divide,
    Modulo,
    Power,
    Equal,
    NotEqual,
    Less,
    LessEqual,
    Greater,
    GreaterEqual,
    And,
    Or,
}
