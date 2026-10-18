mod commands;
mod conllu;
mod document;

use document::AppState;

pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .manage(AppState::new())
        .invoke_handler(tauri::generate_handler![
            commands::api_dispatch,
            commands::open_file,
            commands::save_file,
            commands::save_file_as,
            commands::is_dirty,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
