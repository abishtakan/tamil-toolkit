#[derive(Clone, Copy)]
pub(super) enum Following {
    Tamil,
    Decimal,
}

pub(super) struct Abbreviation {
    pub form: &'static str,
    pub max_bytes: usize,
    pub following: Following,
    pub min_spaces: usize,
    pub punctuation: &'static str,
}

include!(concat!(env!("OUT_DIR"), "/tables.rs"));

pub(super) fn contains(ranges: &[[u32; 2]], scalar: char) -> bool {
    let value = scalar as u32;
    let index = ranges.partition_point(|range| range[1] < value);
    ranges.get(index).is_some_and(|range| range[0] <= value)
}
