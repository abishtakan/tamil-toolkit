use wasm_bindgen::prelude::*;

#[wasm_bindgen]
pub fn execute(request: &str) -> Result<String, JsError> {
    tamil_toolkit::execute_json(request).map_err(|error| JsError::new(&error))
}

#[wasm_bindgen]
pub fn load_lexicon_pack_bytes(bytes: &[u8]) -> Result<String, JsError> {
    tamil_toolkit::lexicon::load_pack_bytes_json(bytes).map_err(|error| JsError::new(&error))
}
