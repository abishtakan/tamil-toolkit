# Contract: GitHub Workflow Updates & OIDC Trusted Publishing

## 1. `publish-release.yml` npm Job Update

### Contract
The `npm` job in `.github/workflows/publish-release.yml` MUST dual-tag the published package with both the channel tag (`alpha`) and `latest` using OIDC trusted publishing.

### Job Specification
```yaml
      - name: Publish the reviewed tarball using OIDC
        env:
          TARBALL: ${{ steps.verify.outputs.tarball }}
          NPM_TAG: ${{ steps.verify.outputs.npm_tag }}
          VERSION: ${{ steps.verify.outputs.version }}
        run: |
          set -euo pipefail
          if python tools/release_policy.py is-published --registry npm --package tamil-toolkit; then
            echo "npm package tamil-toolkit is already published; skipping."
          else
            npm publish "$TARBALL" --tag "$NPM_TAG"
          fi
          # Ensure default npm landing page and 'npm install tamil-toolkit' point to the active release
          npm dist-tag add "tamil-toolkit@$VERSION" latest
```

---

## 2. Dispatch Invocation Contracts

### `alpha-artifacts.yml`
- Dispatch Command: `gh workflow run alpha-artifacts.yml -f source_ref=master`
- Artifacts Output Names:
  - `alpha-rust`: contains all public crate `.crate` files and `release-source.json`
  - `alpha-npm-node22`: contains `tamil-toolkit-<version>.tgz` built on Node 22
  - `alpha-npm-node24`: contains `tamil-toolkit-<version>.tgz` built on Node 24
  - `alpha-python-x86_64-unknown-linux-gnu`: contains Linux wheel + sdist
  - `alpha-python-x86_64-pc-windows-msvc`: contains Windows wheel
  - `alpha-python-aarch64-apple-darwin`: contains macOS Apple Silicon wheel

### `publish-release.yml`
- Dispatch Command: `gh workflow run publish-release.yml -f artifact_run_id=<run_id> -f source_sha=<source_sha> -f confirm_publish=publish`
- Invariant: `confirm_publish` MUST be `'publish'`; any other value causes jobs to skip.
