use std::io::{self, BufRead};

fn main() {
    for line in io::stdin().lock().lines() {
        let response = match line {
            Ok(line) => match tamil_toolkit::execute_json(&line) {
                Ok(result) => result,
                Err(error) => {
                    eprintln!("{error}");
                    std::process::exit(1);
                }
            },
            Err(error) => {
                eprintln!("{error}");
                std::process::exit(1);
            }
        };
        println!("{response}");
    }
}
