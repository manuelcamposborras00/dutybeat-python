# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/) and the project uses [SemVer](https://semver.org/).

## [0.2.1]

### Changed
- Richer editor help: `DutyBeat(...)` and `users.get(...)` now document every parameter (Args), so the
  signature-help popup in VS Code describes each one. No API changes.

## [0.2.0]

### Changed
- `Profile` is now a fully typed dataclass: every field (`dni`, `iban`, `ssn`, `phone_personal`, …) is
  declared, so editors autocomplete them and show help. Item access (`profile["iban"]`) and
  `profile.get(...)` still work; unknown/newer API fields are ignored gracefully. No change for code that
  already used attribute access.

## [0.1.0]

### Added
- `DutyBeat` client with `users.get(user_id, include_folders=...)` for `GET /api/v1/users/:id`.
- Typed models (`User`, `Profile`, `Ref`, `Folder`) and errors (`AuthenticationError`,
  `ForbiddenError`, `NotFoundError`, `RateLimitError`, `APIError`).
- Automatic retries on `429`/`5xx` honouring `Retry-After`.
