use pyo3::{
    exceptions::{PyRecursionError, PyValueError},
    prelude::*,
    types::{PyBool, PyDict, PyFloat, PyInt, PyList, PyString, PyTuple, PyType},
};
use std::collections::HashSet;
use tamil_toolkit::core::audit_tamil_text_light;
use tamil_toolkit::host_batch::{push_ascii_json_str, push_data_json_str, sha256_hex};

type TextAuditPyItem = Option<(bool, Vec<(usize, u32)>, bool)>;

struct ExactTypes<'py> {
    py_str: Bound<'py, PyType>,
    py_int: Bound<'py, PyType>,
    py_bool: Bound<'py, PyType>,
    py_float: Bound<'py, PyType>,
    py_list: Bound<'py, PyType>,
    py_dict: Bound<'py, PyType>,
}

impl<'py> ExactTypes<'py> {
    fn new(py: Python<'py>) -> Self {
        Self {
            py_str: py.get_type::<PyString>(),
            py_int: py.get_type::<PyInt>(),
            py_bool: py.get_type::<PyBool>(),
            py_float: py.get_type::<PyFloat>(),
            py_list: py.get_type::<PyList>(),
            py_dict: py.get_type::<PyDict>(),
        }
    }
}

fn enter_container<'py>(
    obj: &Bound<'py, PyAny>,
    active: &mut HashSet<usize>,
    stack: &mut Vec<(Bound<'py, PyAny>, bool)>,
) -> PyResult<()> {
    if !active.insert(obj.as_ptr() as usize) {
        return Err(PyRecursionError::new_err("cyclic Python container"));
    }
    stack.push((obj.clone(), true));
    Ok(())
}

fn check_no_surrogates_tree<'py>(
    root: &Bound<'py, PyAny>,
    types: &ExactTypes<'py>,
) -> PyResult<bool> {
    let mut stack: Vec<(Bound<'py, PyAny>, bool)> = vec![(root.clone(), false)];
    let mut active = HashSet::new();
    let mut native_ok = true;

    while let Some((obj, leaving)) = stack.pop() {
        if leaving {
            active.remove(&(obj.as_ptr() as usize));
            continue;
        }
        if obj.is_none() {
            continue;
        }
        let tp = obj.get_type();
        if tp.is(&types.py_str) {
            if obj.cast::<PyString>()?.to_cow().is_err() {
                return Err(PyValueError::new_err(
                    "invalid Unicode scalar: lone surrogate",
                ));
            }
        } else if tp.is(&types.py_int) || tp.is(&types.py_bool) {
            continue;
        } else if tp.is(&types.py_float) {
            let val: f64 = obj.extract()?;
            if !val.is_finite() {
                native_ok = false;
            }
        } else if tp.is(&types.py_list) {
            enter_container(&obj, &mut active, &mut stack)?;
            let list = obj.cast::<PyList>()?;
            for item in list.iter() {
                stack.push((item, false));
            }
        } else if tp.is(&types.py_dict) {
            enter_container(&obj, &mut active, &mut stack)?;
            let dict = obj.cast::<PyDict>()?;
            for (k, v) in dict.iter() {
                if !k.get_type().is(&types.py_str) {
                    native_ok = false;
                }
                stack.push((k, false));
                stack.push((v, false));
            }
        } else if obj.is_instance(&types.py_str)? {
            native_ok = false;
            if obj.cast::<PyString>()?.to_cow().is_err() {
                return Err(PyValueError::new_err(
                    "invalid Unicode scalar: lone surrogate",
                ));
            }
        } else if obj.is_instance(&types.py_list)? || obj.is_instance_of::<PyTuple>() {
            native_ok = false;
            enter_container(&obj, &mut active, &mut stack)?;
            for item in obj.try_iter()? {
                stack.push((item?, false));
            }
        } else if obj.is_instance(&types.py_dict)? {
            native_ok = false;
            enter_container(&obj, &mut active, &mut stack)?;
            let items = obj.call_method0("items")?;
            for pair in items.try_iter()? {
                let pair = pair?;
                let mut pair_items = pair.try_iter()?;
                let key = pair_items.next().transpose()?.ok_or_else(|| {
                    PyValueError::new_err("not enough values to unpack (expected 2)")
                })?;
                let value = pair_items.next().transpose()?.ok_or_else(|| {
                    PyValueError::new_err("not enough values to unpack (expected 2)")
                })?;
                if pair_items.next().transpose()?.is_some() {
                    return Err(PyValueError::new_err(
                        "too many values to unpack (expected 2)",
                    ));
                }
                stack.push((key, false));
                stack.push((value, false));
            }
        } else {
            native_ok = false;
        }
    }

    Ok(native_ok)
}

fn serialize_canonical_json<'py>(
    obj: &Bound<'py, PyAny>,
    ascii_mode: bool,
    buf: &mut Vec<u8>,
    types: &ExactTypes<'py>,
    depth: usize,
) -> PyResult<bool> {
    if depth > 64 {
        return Ok(false);
    }
    if obj.is_none() {
        buf.extend_from_slice(b"null");
        return Ok(true);
    }
    let tp = obj.get_type();
    if tp.is(&types.py_bool) {
        let val: bool = obj.extract()?;
        buf.extend_from_slice(if val { b"true" } else { b"false" });
        return Ok(true);
    }
    if tp.is(&types.py_int) {
        if let Ok(val) = obj.extract::<i64>() {
            let mut itoa_buf = [0u8; 24];
            let formatted = format_i64_into(val, &mut itoa_buf);
            buf.extend_from_slice(formatted);
            return Ok(true);
        }
        return Ok(false);
    }
    if tp.is(&types.py_str) {
        let Ok(cow) = obj.cast::<PyString>()?.to_cow() else {
            return Ok(false);
        };
        if ascii_mode {
            push_ascii_json_str(buf, cow.as_ref());
        } else {
            push_data_json_str(buf, cow.as_ref());
        }
        return Ok(true);
    }
    if tp.is(&types.py_list) {
        let list = obj.cast::<PyList>()?;
        buf.push(b'[');
        for (idx, item) in list.iter().enumerate() {
            if idx > 0 {
                buf.push(b',');
            }
            if !serialize_canonical_json(&item, ascii_mode, buf, types, depth + 1)? {
                return Ok(false);
            }
        }
        buf.push(b']');
        return Ok(true);
    }
    if tp.is(&types.py_dict) {
        let dict = obj.cast::<PyDict>()?;
        let mut entries: Vec<(String, Bound<'py, PyAny>)> = Vec::with_capacity(dict.len());
        for (k, v) in dict.iter() {
            if !k.get_type().is(&types.py_str) {
                return Ok(false);
            }
            let k_str = k.cast_into::<PyString>()?;
            let Ok(k_cow) = k_str.to_cow() else {
                return Ok(false);
            };
            entries.push((k_cow.into_owned(), v));
        }
        entries.sort_unstable_by(|(a, _), (b, _)| a.cmp(b));
        buf.push(b'{');
        for (idx, (k, v)) in entries.iter().enumerate() {
            if idx > 0 {
                buf.push(b',');
            }
            if ascii_mode {
                push_ascii_json_str(buf, k.as_str());
            } else {
                push_data_json_str(buf, k.as_str());
            }
            buf.push(b':');
            if !serialize_canonical_json(v, ascii_mode, buf, types, depth + 1)? {
                return Ok(false);
            }
        }
        buf.push(b'}');
        return Ok(true);
    }
    Ok(false)
}

#[inline]
fn format_i64_into(mut val: i64, buf: &mut [u8; 24]) -> &[u8] {
    if val == 0 {
        buf[0] = b'0';
        return &buf[..1];
    }
    let neg = val < 0;
    let mut mag: u64 = if neg {
        val.wrapping_neg() as u64
    } else {
        val as u64
    };
    let mut pos = buf.len();
    while mag > 0 {
        pos -= 1;
        buf[pos] = b'0' + (mag % 10) as u8;
        mag /= 10;
    }
    if neg {
        pos -= 1;
        buf[pos] = b'-';
    }
    let _ = &mut val;
    &buf[pos..]
}

#[pyfunction]
fn execute(request: &str) -> PyResult<String> {
    tamil_toolkit::execute_json(request).map_err(PyValueError::new_err)
}

#[pyfunction]
fn batch_audit_tamil_texts(texts: &Bound<'_, PyAny>) -> PyResult<Vec<TextAuditPyItem>> {
    let mut out = Vec::new();
    for item in texts.try_iter()? {
        let item = item?;
        let py_str = item.cast::<PyString>()?;
        match py_str.to_cow() {
            Ok(cow) => {
                let audit = audit_tamil_text_light(cow.as_ref());
                out.push(Some((
                    audit.is_nfc,
                    audit.intentional_controls,
                    audit.has_other_tamil_cluster,
                )));
            }
            Err(_) => out.push(None),
        }
    }
    Ok(out)
}

#[pyfunction]
fn batch_check_no_surrogates<'py>(
    py: Python<'py>,
    rows: &Bound<'py, PyAny>,
) -> PyResult<Vec<bool>> {
    let types = ExactTypes::new(py);
    let mut out = Vec::new();
    for row in rows.try_iter()? {
        let row = row?;
        out.push(check_no_surrogates_tree(&row, &types)?);
    }
    Ok(out)
}

#[pyfunction]
fn batch_canonical_json_sha256<'py>(
    py: Python<'py>,
    values: &Bound<'py, PyAny>,
) -> PyResult<Vec<Option<String>>> {
    let types = ExactTypes::new(py);
    let mut out = Vec::new();
    let mut buf = Vec::with_capacity(512);
    for value in values.try_iter()? {
        let value = value?;
        buf.clear();
        if serialize_canonical_json(&value, true, &mut buf, &types, 0)? {
            out.push(Some(sha256_hex(&buf)));
        } else {
            out.push(None);
        }
    }
    Ok(out)
}

#[pyfunction]
fn batch_data_json<'py>(
    py: Python<'py>,
    values: &Bound<'py, PyAny>,
) -> PyResult<Vec<Option<String>>> {
    let types = ExactTypes::new(py);
    let mut out = Vec::new();
    let mut buf = Vec::with_capacity(512);
    for value in values.try_iter()? {
        let value = value?;
        buf.clear();
        if serialize_canonical_json(&value, false, &mut buf, &types, 0)? {
            let text = String::from_utf8(buf.clone())
                .map_err(|err| PyValueError::new_err(err.to_string()))?;
            out.push(Some(text));
        } else {
            out.push(None);
        }
    }
    Ok(out)
}

#[pymodule]
fn _native(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add("HOST_BATCH_OPTIMIZED", !cfg!(debug_assertions))?;
    module.add_function(wrap_pyfunction!(execute, module)?)?;
    module.add_function(wrap_pyfunction!(batch_audit_tamil_texts, module)?)?;
    module.add_function(wrap_pyfunction!(batch_check_no_surrogates, module)?)?;
    module.add_function(wrap_pyfunction!(batch_canonical_json_sha256, module)?)?;
    module.add_function(wrap_pyfunction!(batch_data_json, module)?)?;
    Ok(())
}
