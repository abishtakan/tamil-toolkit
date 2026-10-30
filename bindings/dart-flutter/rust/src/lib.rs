//! Minimal C ABI. The caller owns input; Rust owns the returned string until free.
use std::ffi::{c_char, CStr, CString};

/// Dispatch UTF-8 JSON. Always release a non-null result with tamil_toolkit_free.
///
/// # Safety
/// `request` must be null or point to a live, NUL-terminated readable C string.
#[no_mangle]
pub unsafe extern "C" fn tamil_toolkit_call(request: *const c_char) -> *mut c_char {
    let response = std::panic::catch_unwind(|| {
        let result = if request.is_null() {
            Err("null request".to_owned())
        } else {
            // SAFETY: the caller guarantees the lifetime and NUL termination above.
            unsafe { CStr::from_ptr(request) }
                .to_str()
                .map_err(|e| e.to_string())
                .and_then(tamil_toolkit::execute_json)
        };
        match result {
            Ok(json) => format!("{{\"ok\":{json}}}"),
            Err(error) => serde_json::json!({"error": error}).to_string(),
        }
    })
    .unwrap_or_else(|_| "{\"error\":\"Rust panic caught at FFI boundary\"}".to_owned());
    // JSON serialization escapes embedded NUL characters.
    CString::new(response)
        .expect("JSON contains no literal NUL")
        .into_raw()
}

/// Release exactly one result previously returned by tamil_toolkit_call.
///
/// # Safety
/// `response` must be null or an unfreed pointer returned by tamil_toolkit_call.
#[no_mangle]
pub unsafe extern "C" fn tamil_toolkit_free(response: *mut c_char) {
    if !response.is_null() {
        // SAFETY: ownership of this Rust allocation is returned by the caller.
        drop(unsafe { CString::from_raw(response) });
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn roundtrip_and_free() {
        let input = CString::new(r#"{"op":"get_letters","input":"a"}"#).unwrap();
        // SAFETY: input is live and NUL-terminated; returned pointers are used once.
        unsafe {
            let output = tamil_toolkit_call(input.as_ptr());
            assert_eq!(CStr::from_ptr(output).to_str().unwrap(), r#"{"ok":["a"]}"#);
            tamil_toolkit_free(output);
            let output = tamil_toolkit_call(std::ptr::null());
            assert!(CStr::from_ptr(output).to_str().unwrap().contains("error"));
            tamil_toolkit_free(output);
            tamil_toolkit_free(std::ptr::null_mut());
        }
    }
}
