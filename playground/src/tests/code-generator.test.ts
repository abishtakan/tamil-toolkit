import { describe, it, expect } from "vitest";

describe("T025: CodeGenerator", () => {
  it("generates TypeScript snippet", () => {
    const tsCode = `import { to_words } from "tamil-toolkit/web";\nconsole.log(to_words(125000));`;
    expect(tsCode).toContain("tamil-toolkit/web");
    expect(tsCode).toContain("to_words");
  });

  it("generates Python snippet", () => {
    const pyCode = `import tamil_toolkit\nprint(tamil_toolkit.to_words(125000))`;
    expect(pyCode).toContain("tamil_toolkit");
    expect(pyCode).toContain("to_words");
  });

  it("generates Rust snippet", () => {
    const rustCode = `use tamil_toolkit::to_words;\nfn main() { println!("{}", to_words(125000)); }`;
    expect(rustCode).toContain("tamil_toolkit::to_words");
  });

  it("generates Dart snippet", () => {
    const dartCode = `import 'package:tamil_toolkit/tamil_toolkit.dart';\nvoid main() { print(TamilToolkit().toWords(125000)); }`;
    expect(dartCode).toContain("tamil_toolkit");
  });
});
