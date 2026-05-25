use pyo3::prelude::*;
use jwalk::WalkDir;
use std::time::UNIX_EPOCH;
use std::path::Path;

#[pyfunction]
pub fn scan_workspace_files(ws_root: &str) -> PyResult<Vec<(String, String, u64, f64)>> {
    let mut results = Vec::new();
    let root_path = Path::new(ws_root);

    // Run parallel directory traversal using jwalk
    for entry in WalkDir::new(root_path)
        .skip_hidden(false) // We manually filter hidden files
        .process_read_dir(|_, _, _, dir_entry_results| {
            dir_entry_results.retain(|dir_entry_result| {
                dir_entry_result.as_ref().map(|dir_entry| {
                    let file_name = dir_entry.file_name().to_string_lossy();
                    // Prune hidden or system directories (starting with . or $)
                    !(dir_entry.file_type().is_dir() && (file_name.starts_with('.') || file_name.starts_with('$')))
                }).unwrap_or(true)
            });
        }) 
    {
        if let Ok(dir_entry) = entry {
            if dir_entry.file_type().is_file() {
                let file_name = dir_entry.file_name().to_string_lossy();
                
                // Skip internal config/database files
                if file_name.starts_with('.') || file_name == ".docman.db" || file_name == ".config.json" || file_name.starts_with("~$") {
                    continue;
                }
                
                let rel_path_res = dir_entry.path().strip_prefix(root_path)
                    .map(|p| p.to_string_lossy().replace("\\", "/"));
                    
                if let Ok(rel_path) = rel_path_res {
                    let mut size = 0;
                    let mut mtime = 0.0;
                    
                    if let Ok(metadata) = dir_entry.metadata() {
                        size = metadata.len();
                        if let Ok(modified) = metadata.modified() {
                            if let Ok(duration) = modified.duration_since(UNIX_EPOCH) {
                                mtime = duration.as_secs_f64();
                            } else if let Ok(duration) = UNIX_EPOCH.duration_since(modified) {
                                mtime = -duration.as_secs_f64();
                            }
                        }
                    }
                    
                    results.push((rel_path, file_name.to_string(), size, mtime));
                }
            }
        }
    }
    
    Ok(results)
}
