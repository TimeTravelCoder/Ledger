use pyo3::prelude::*;

mod semantic;
mod scanner;

use semantic::recommend_tags;
use scanner::scan_workspace_files;

#[pymodule]
fn ledger_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(recommend_tags, m)?)?;
    m.add_function(wrap_pyfunction!(scan_workspace_files, m)?)?;
    Ok(())
}
