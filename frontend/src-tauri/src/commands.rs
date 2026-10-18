use serde_json::{json, Value};
use std::collections::HashMap;
use std::fs;
use tauri::State;
use tauri_plugin_dialog::DialogExt;

use crate::conllu::{self, WordLine};
use crate::document::{AppState, Document};

/// Synthetic IDs for offline mode. The treebank ID is always 1,
/// annotation IDs are the sentence order (1-based).

/// Main dispatch: maps REST-style method+path into local document operations.
#[tauri::command]
pub async fn api_dispatch(
    state: State<'_, AppState>,
    method: String,
    path: String,
    body: Option<String>,
) -> Result<Value, String> {
    let method = method.to_uppercase();
    let path = path.trim_end_matches('/');

    // --- Auth ---
    if path == "/auth/me" && method == "GET" {
        return Ok(json!({
            "id": 0,
            "username": "local",
            "email": "",
            "first_name": "Local",
            "last_name": "User",
            "is_active": true,
            "preferences": {
                "graph_preference": 1,
                "error_condition": false,
                "current_columns": ["id_f","form","lemma","upos","xpos","feats","head","deprel","deps","misc"]
            }
        }));
    }

    // --- Languages ---
    if path == "/treebanks/languages" && method == "GET" {
        return Ok(json!({"tr": "Turkish", "en": "English", "ar": "Arabic", "de": "German"}));
    }

    // --- Treebanks ---
    if path == "/treebanks" && method == "GET" {
        let doc = state.document.lock().map_err(|e| e.to_string())?;
        match doc.as_ref() {
            Some(doc) => {
                let count = doc.sentences.len();
                Ok(json!([{
                    "id": 1,
                    "title": doc.title,
                    "language": doc.language,
                    "created_at": "1970-01-01T00:00:00",
                    "sentence_count": count,
                    "annotation_count": count,
                    "complete_count": 0
                }]))
            }
            None => Ok(json!([])),
        }
    }
    // GET /treebanks/by-title/:title
    else if path.starts_with("/treebanks/by-title/") && method == "GET" {
        let doc = state.document.lock().map_err(|e| e.to_string())?;
        match doc.as_ref() {
            Some(doc) => Ok(json!({
                "id": 1,
                "title": doc.title,
                "language": doc.language,
                "created_at": "1970-01-01T00:00:00"
            })),
            None => Err("No document open".to_string()),
        }
    }
    // GET /treebanks/:id/sentences
    else if path.ends_with("/sentences") && path.starts_with("/treebanks/") && method == "GET" {
        let doc = state.document.lock().map_err(|e| e.to_string())?;
        match doc.as_ref() {
            Some(doc) => {
                let briefs: Vec<Value> = doc
                    .sentences
                    .iter()
                    .map(|s| {
                        json!({
                            "id": s.order,
                            "order": s.order,
                            "sent_id": s.sent_id,
                            "text": s.text
                        })
                    })
                    .collect();
                Ok(json!(briefs))
            }
            None => Err("No document open".to_string()),
        }
    }
    // --- Annotations ---
    // GET /annotations/by-position/?treebank_id=&order=
    else if path.starts_with("/annotations/by-position") && method == "GET" {
        let params = parse_query_string(&path);
        let order: usize = params
            .get("order")
            .and_then(|v| v.parse().ok())
            .ok_or("Missing or invalid 'order' parameter")?;

        let doc = state.document.lock().map_err(|e| e.to_string())?;
        let doc = doc.as_ref().ok_or("No document open")?;
        let sent = doc
            .sentences
            .iter()
            .find(|s| s.order == order)
            .ok_or(format!("Sentence with order {} not found", order))?;

        Ok(sentence_to_annotation_detail(sent, &doc.title))
    }
    // GET /annotations/mine
    else if path == "/annotations/mine" || path.starts_with("/annotations/mine/") && method == "GET"
    {
        let doc = state.document.lock().map_err(|e| e.to_string())?;
        match doc.as_ref() {
            Some(doc) => {
                let details: Vec<Value> = doc
                    .sentences
                    .iter()
                    .map(|s| sentence_to_annotation_detail(s, &doc.title))
                    .collect();
                Ok(json!(details))
            }
            None => Ok(json!([])),
        }
    }
    // PUT /wordlines/annotations/:id
    else if path.starts_with("/wordlines/annotations/") && method == "PUT" {
        let id_str = path.strip_prefix("/wordlines/annotations/").unwrap();
        let order: usize = id_str.parse().map_err(|_| "Invalid annotation ID")?;

        let body_str = body.ok_or("Missing request body")?;
        let body_val: Value =
            serde_json::from_str(&body_str).map_err(|e| format!("Invalid JSON: {}", e))?;

        let new_wordlines: Vec<WordLine> = serde_json::from_value(
            body_val
                .get("wordlines")
                .cloned()
                .ok_or("Missing 'wordlines' field")?,
        )
        .map_err(|e| format!("Invalid wordlines: {}", e))?;

        let mut doc = state.document.lock().map_err(|e| e.to_string())?;
        let doc = doc.as_mut().ok_or("No document open")?;
        let sent = doc
            .sentences
            .iter_mut()
            .find(|s| s.order == order)
            .ok_or(format!("Sentence with order {} not found", order))?;

        sent.wordlines = new_wordlines;
        doc.dirty = true;

        // Return updated wordlines in the format the frontend expects
        let wl_response: Vec<Value> = sent
            .wordlines
            .iter()
            .enumerate()
            .map(|(i, wl)| wordline_to_read(wl, order, i))
            .collect();
        Ok(json!(wl_response))
    }
    // PATCH /annotations/:id
    else if path.starts_with("/annotations/") && method == "PATCH" {
        let id_str = path.strip_prefix("/annotations/").unwrap();
        let order: usize = id_str.parse().map_err(|_| "Invalid annotation ID")?;

        // We accept status/notes but for offline mode we just acknowledge
        let doc = state.document.lock().map_err(|e| e.to_string())?;
        let doc = doc.as_ref().ok_or("No document open")?;
        let sent = doc
            .sentences
            .iter()
            .find(|s| s.order == order)
            .ok_or(format!("Sentence with order {} not found", order))?;

        Ok(json!({
            "id": sent.order,
            "sentence_id": sent.order,
            "annotator_id": 0,
            "status": 0,
            "is_template": false,
            "is_gold": false,
            "notes": "",
            "created_at": "1970-01-01T00:00:00"
        }))
    }
    // GET /annotations/:id
    else if path.starts_with("/annotations/") && method == "GET" {
        let id_str = path.strip_prefix("/annotations/").unwrap();
        let order: usize = id_str.parse().map_err(|_| "Invalid annotation ID")?;

        let doc = state.document.lock().map_err(|e| e.to_string())?;
        let doc = doc.as_ref().ok_or("No document open")?;
        let sent = doc
            .sentences
            .iter()
            .find(|s| s.order == order)
            .ok_or(format!("Sentence with order {} not found", order))?;

        Ok(sentence_to_annotation_detail(sent, &doc.title))
    }
    else {
        Err(format!(
            "Offline mode: {} {} not supported",
            method, path
        ))
    }
}

/// Open a CoNLL-U file via native dialog.
#[tauri::command]
pub async fn open_file(
    app: tauri::AppHandle,
    state: State<'_, AppState>,
) -> Result<Value, String> {
    let file_path = app
        .dialog()
        .file()
        .add_filter("CoNLL-U files", &["conllu"])
        .blocking_pick_file()
        .ok_or("No file selected")?;

    let path = file_path.into_path().map_err(|e| format!("Invalid file path: {}", e))?;
    let content = fs::read_to_string(&path)
        .map_err(|e| format!("Failed to read file: {}", e))?;

    let sentences = conllu::parse(&content);
    if sentences.is_empty() {
        return Err("No sentences found in file".to_string());
    }

    let doc = Document::new(path.clone(), sentences);
    let title = doc.title.clone();
    let sentence_count = doc.sentences.len();

    let mut state_doc = state.document.lock().map_err(|e| e.to_string())?;
    *state_doc = Some(doc);

    Ok(json!({
        "title": title,
        "path": path.to_string_lossy(),
        "sentence_count": sentence_count
    }))
}

/// Save the current document to its file path.
#[tauri::command]
pub async fn save_file(state: State<'_, AppState>) -> Result<(), String> {
    let mut doc = state.document.lock().map_err(|e| e.to_string())?;
    let doc = doc.as_mut().ok_or("No document open")?;
    let path = doc.file_path.as_ref().ok_or("No file path set")?;

    let content = conllu::export(&doc.sentences);
    fs::write(path, &content).map_err(|e| format!("Failed to write file: {}", e))?;
    doc.dirty = false;

    Ok(())
}

/// Save the current document to a new path via native dialog.
#[tauri::command]
pub async fn save_file_as(
    app: tauri::AppHandle,
    state: State<'_, AppState>,
) -> Result<String, String> {
    let file_path = app
        .dialog()
        .file()
        .add_filter("CoNLL-U files", &["conllu"])
        .blocking_save_file()
        .ok_or("No file selected")?;

    let path = file_path.into_path().map_err(|e| format!("Invalid file path: {}", e))?;

    let mut doc = state.document.lock().map_err(|e| e.to_string())?;
    let doc = doc.as_mut().ok_or("No document open")?;

    let content = conllu::export(&doc.sentences);
    fs::write(&path, &content).map_err(|e| format!("Failed to write file: {}", e))?;

    doc.file_path = Some(path.clone());
    doc.title = path
        .file_stem()
        .map(|s: &std::ffi::OsStr| s.to_string_lossy().to_string())
        .unwrap_or_else(|| "Untitled".to_string());
    doc.dirty = false;

    Ok(path.to_string_lossy().to_string())
}

/// Check if the current document has unsaved changes.
#[tauri::command]
pub async fn is_dirty(state: State<'_, AppState>) -> Result<bool, String> {
    let doc = state.document.lock().map_err(|e| e.to_string())?;
    Ok(doc.as_ref().map_or(false, |d| d.dirty))
}

// --- Helper functions ---

/// Parse query string parameters from a path like "/foo?bar=1&baz=2"
fn parse_query_string(path: &str) -> HashMap<String, String> {
    let mut params = HashMap::new();
    if let Some(query) = path.split('?').nth(1) {
        for pair in query.split('&') {
            if let Some((key, value)) = pair.split_once('=') {
                params.insert(key.to_string(), value.to_string());
            }
        }
    }
    params
}

/// Convert a Sentence to the AnnotationDetail JSON the frontend expects.
fn sentence_to_annotation_detail(sent: &conllu::Sentence, treebank_title: &str) -> Value {
    let wordlines: Vec<Value> = sent
        .wordlines
        .iter()
        .enumerate()
        .map(|(i, wl)| wordline_to_read(wl, sent.order, i))
        .collect();

    json!({
        "id": sent.order,
        "sentence_id": sent.order,
        "annotator_id": 0,
        "status": 0,
        "is_template": false,
        "is_gold": false,
        "notes": "",
        "created_at": "1970-01-01T00:00:00",
        "wordlines": wordlines,
        "annotator_username": "local",
        "sentence_sent_id": sent.sent_id,
        "sentence_text": sent.text,
        "sentence_metadata": if sent.comments.is_empty() { Value::Null } else { json!(sent.comments) },
        "treebank_title": treebank_title,
        "treebank_id": 1,
        "sentence_order": sent.order
    })
}

/// Convert a WordLine to the WordLineRead JSON the frontend expects.
fn wordline_to_read(wl: &conllu::WordLine, annotation_id: usize, index: usize) -> Value {
    json!({
        "id": index + 1,
        "annotation_id": annotation_id,
        "id_f": wl.id_f,
        "form": wl.form,
        "lemma": wl.lemma,
        "upos": wl.upos,
        "xpos": wl.xpos,
        "feats": wl.feats,
        "head": wl.head,
        "deprel": wl.deprel,
        "deps": wl.deps,
        "misc": wl.misc,
        "feats_parsed": parse_pipe_field(&wl.feats),
        "misc_parsed": parse_pipe_field(&wl.misc)
    })
}

/// Parse a pipe-separated field like "Case=Nom|Number=Sing" into a JSON object.
fn parse_pipe_field(field: &str) -> Value {
    if field == "_" || field.is_empty() {
        return Value::Null;
    }
    let mut map = serde_json::Map::new();
    for pair in field.split('|') {
        if let Some((key, value)) = pair.split_once('=') {
            map.insert(key.to_string(), Value::String(value.to_string()));
        }
    }
    if map.is_empty() {
        Value::Null
    } else {
        Value::Object(map)
    }
}
