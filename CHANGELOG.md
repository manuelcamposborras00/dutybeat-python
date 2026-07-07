# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/) and the project uses [SemVer](https://semver.org/).

## [0.1.0] - Unreleased

### Added
- `DutyBeat` client with `users.get(user_id, include_folders=...)` for `GET /api/v1/users/:id`.
- Typed models (`User`, `Profile`, `Ref`, `Folder`) and errors (`AuthenticationError`,
  `ForbiddenError`, `NotFoundError`, `RateLimitError`, `APIError`).
- Automatic retries on `429`/`5xx` honouring `Retry-After`.
