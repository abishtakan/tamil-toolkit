## Change

Describe the behavior and its specification or acceptance criteria.

## Verification

Record the relevant commands, outcomes, and any checks still pending.

- [ ] Sourced fixtures/data precede changed linguistic behavior.
- [ ] Rust and affected bindings consume the same active golden vectors.
- [ ] Generated distribution copies and release policy checks pass.
- [ ] Local integration gate and affected Dart checks pass.
- [ ] Unreleased notes and project handoff reflect the change.

## Release impact

State API/version, package-scope, channel, licensing, or platform changes.
Link the release review if changing release-policy.toml. Ordinary merges do
not publish packages; deferred packages remain private.
