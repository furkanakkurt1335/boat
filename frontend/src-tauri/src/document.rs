use std::path::PathBuf;
use std::sync::Mutex;

use crate::conllu::Sentence;

/// A single open document (CoNLL-U file loaded from disk).
pub struct Document {
    pub file_path: Option<PathBuf>,
    pub title: String,
    pub language: String,
    pub sentences: Vec<Sentence>,
    pub dirty: bool,
}

impl Document {
    pub fn new(file_path: PathBuf, sentences: Vec<Sentence>) -> Self {
        let title = file_path
            .file_stem()
            .map(|s| s.to_string_lossy().to_string())
            .unwrap_or_else(|| "Untitled".to_string());
        Self {
            file_path: Some(file_path),
            title,
            language: "unknown".to_string(),
            sentences,
            dirty: false,
        }
    }
}

/// Application state managed by Tauri — holds the currently open document.
pub struct AppState {
    pub document: Mutex<Option<Document>>,
}

impl AppState {
    pub fn new() -> Self {
        Self {
            document: Mutex::new(None),
        }
    }
}
