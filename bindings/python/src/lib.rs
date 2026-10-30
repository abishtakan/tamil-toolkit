use pyo3::{exceptions::PyValueError, prelude::*};

#[pyfunction]
fn execute(request: &str) -> PyResult<String> {
    tamil_toolkit::execute_json(request).map_err(PyValueError::new_err)
}

#[pymodule]
fn _native(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_function(wrap_pyfunction!(execute, module)?)
}
