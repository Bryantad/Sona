use std::fs;
use std::path::{Path, PathBuf};

#[derive(Clone, Debug)]
pub struct SourceFile {
    pub id: usize,
    pub path: PathBuf,
    pub text: String,
    line_starts: Vec<usize>,
}

impl SourceFile {
    pub fn new(id: usize, path: impl Into<PathBuf>, text: impl Into<String>) -> Self {
        let text = text.into();
        let mut line_starts = vec![0];
        for (offset, ch) in text.char_indices() {
            if ch == '\n' {
                line_starts.push(offset + 1);
            }
        }
        Self {
            id,
            path: path.into(),
            text,
            line_starts,
        }
    }

    pub fn read(id: usize, path: impl AsRef<Path>) -> std::io::Result<Self> {
        let path = path.as_ref();
        let text = fs::read_to_string(path)?;
        Ok(Self::new(id, path.to_path_buf(), text))
    }

    pub fn display_name(&self) -> String {
        self.path.display().to_string()
    }

    pub fn line_column(&self, byte_offset: usize) -> (usize, usize) {
        let line_index = match self.line_starts.binary_search(&byte_offset) {
            Ok(index) => index,
            Err(index) => index.saturating_sub(1),
        };
        let line_start = *self.line_starts.get(line_index).unwrap_or(&0);
        (line_index + 1, byte_offset.saturating_sub(line_start) + 1)
    }
}
