export function createManifest(target: "chrome" | "firefox", version?: string): Record<string, any>;
export function writeManifest(target: "chrome" | "firefox"): string;
