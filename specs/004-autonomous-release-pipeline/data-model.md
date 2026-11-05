# Data Model: Autonomous Release Pipeline & npm Dist-Tag Management

## Entities & Schemas

### 1. `ReleaseVersion`

Represents a validated semantic version conforming to repository policy (`X.Y.Z[-channel.N]`).

| Field | Type | Description | Example |
| :--- | :--- | :--- | :--- |
| `version` | String | Full workspace version string | `"0.1.0-alpha.6"` |
| `base` | String | Core semantic version | `"0.1.0"` |
| `stage` | Optional[String] | Prerelease stage tag | `"alpha"` |
| `number` | Optional[String] | Prerelease sequence number | `"6"` |
| `channel` | String | Release channel | `"alpha"` |
| `python_version` | String | PEP 440 normalized version | `"0.1.0a6"` |
| `npm_tag` | String | npm publication dist-tag | `"alpha"` |
| `record_name` | String | Release record file stem | `"alpha-6"` |
| `git_tag` | String | Immutable git tag | `"v0.1.0-alpha.6"` |

---

### 2. `PipelineStage`

Represents the state machine of the release pipeline execution.

```text
[Initial / Dirty Check]
         │
         ▼
[Preflight Passed] ──(prepare version)──► [Version Bumped]
                                                  │
                                                  ▼
                                          [Commit & Push]
                                                  │
                                                  ▼
                                       [Artifact Build Triggered]
                                                  │
                                                  ▼
                                       [Artifact Build Verified]
                                           │               │
                            (if --dry-run) │               │ (normal)
                                           ▼               ▼
                                      [Stopped]    [Publish Triggered]
                                                           │
                                                           ▼
                                                    [Publish Verified]
                                                           │
                                                           ▼
                                                   [Record Committed]
                                                           │
                                                           ▼
                                                    [Tags Pushed]
```

---

### 3. `ArtifactRunManifest`

Represents a successful run of `alpha-artifacts.yml` on GitHub Actions.

| Field | Type | Description |
| :--- | :--- | :--- |
| `run_id` | String / int | GitHub Actions workflow run database ID (e.g. `41409101149`) |
| `head_sha` | String | 40-character commit SHA that was compiled |
| `html_url` | String | Web URL to view run execution logs |
| `status` | String | Execution lifecycle status (`"completed"`) |
| `conclusion` | String | Final run result (`"success"`) |
| `artifacts` | List[String] | Downloadable artifact bundles (`alpha-rust`, `alpha-npm-node22`, `alpha-python-*`) |

---

### 4. `DistTagState`

Represents npm dist-tag mapping state for package `tamil-toolkit`.

| Tag | Pinned Version | Target State | Notes |
| :--- | :--- | :--- | :--- |
| `latest` | `0.1.0-alpha.1` (stale) | Current active release (`0.1.0-alpha.5` or newer) | Determines the npm homepage version and default `npm install` target |
| `alpha` | Current active release | Tracks newest release on alpha channel | Channel-specific installer target |
