use wasm_bindgen::prelude::*;

#[wasm_bindgen]
pub fn execute(request: &str) -> Result<String, JsError> {
    tamil_toolkit::execute_json(request).map_err(|error| JsError::new(&error))
}
