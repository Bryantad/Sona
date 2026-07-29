use sona_ast::Program;
use sona_diagnostics::SonaResult;

#[derive(Clone, Debug, PartialEq)]
pub struct IrProgram {
    pub program: Program,
}

pub fn lower(program: Program) -> SonaResult<IrProgram> {
    Ok(IrProgram { program })
}
