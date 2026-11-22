import { describe, expect, it } from "vitest";
import { createManifest } from "../scripts/build-manifests.mjs";

describe("Dual-browser MV3 manifests", () => {
  it("Chrome manifest has zero install-time host_permissions and required Chrome-only entries", () => {
    const m = createManifest("chrome", "0.1.0");
    expect(m.manifest_version).toBe(3);
    expect("host_permissions" in m).toBe(false);
    expect(m.optional_host_permissions).toEqual(["https://*/*", "http://*/*"]);
    expect(m.permissions).toContain("activeTab");
    expect(m.permissions).toContain("scripting");
    expect(m.permissions).toContain("sidePanel");
    expect(m.permissions).toContain("offscreen");
    expect(m.side_panel?.default_path).toBe("panel.html");
    expect(m.action?.default_popup).toBe("popup.html");
    expect(m.background?.service_worker).toBe("background.js");
    expect("sidebar_action" in m).toBe(false);
    expect(m.commands?.["toggle-live-typing"]?.suggested_key?.default).toBe("Alt+Shift+L");
    expect(m.content_security_policy?.extension_pages).toContain("'wasm-unsafe-eval'");
  });

  it("Firefox manifest uses sidebar_action, non-persistent background scripts, and zero data collection", () => {
    const m = createManifest("firefox", "0.1.0");
    expect(m.manifest_version).toBe(3);
    expect("host_permissions" in m).toBe(false);
    expect(m.permissions).not.toContain("sidePanel");
    expect(m.permissions).not.toContain("offscreen");
    expect(m.sidebar_action?.default_panel).toBe("panel.html");
    expect(m.sidebar_action?.open_at_install).toBe(false);
    expect(m.background?.scripts).toEqual(["background.js"]);
    expect(m.browser_specific_settings?.gecko?.strict_min_version).toBe("140.0");
    expect(m.browser_specific_settings?.gecko?.data_collection_permissions?.required).toEqual(["none"]);
  });
});
