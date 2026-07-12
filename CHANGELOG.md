# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/) and the project uses [SemVer](https://semver.org/).

## [0.20.0]

### Added
- `absences.create(user_id=..., type=..., start_date=..., end_date=...)` for `POST /api/v1/absences`
  (Create Absence): registers an absence on behalf of an employee; enters pending or approved per type.
- `absences.decide(absence_id, decision, note=...)` for `POST /api/v1/absences/:id/decide` (Decide
  Absence): approve/reject a pending absence. Both require the corresponding method on the key.

## [0.19.0]

### Added
- `users.update(user_id, **fields)` for `PATCH /api/v1/users/:user_id` (Update User): partial edit of an
  employee's account and profile fields. Only the fields passed are changed. Profile columns go via
  `**profile_fields`. Returns the updated `User`. Requires the `users.update` method on the key.

## [0.18.0]

### Added
- `users.deactivate(user_id)` for `POST /api/v1/users/:user_id/deactivate` (Deactivate User): disables an
  employee (offboarding); their sessions are revoked. Idempotent. Returns the `User` with
  `status="disabled"`. Requires the `users.deactivate` method on the key.

## [0.17.0]

### Added
- `users.create(email=..., full_name=..., ...)` for `POST /api/v1/users` (Create User): provisions an
  employee (account fields). `password` is optional — omit it and the employee sets it via "forgot
  password". Returns the created `User`. Requires the `users.create` method on the key.

## [0.16.0]

### Added
- `me().acts_as_user` on `GET /api/v1/me` (Whoami): the user the key acts as (whose permissions
  authorize its writes), as a new `ActingUser` model (`.id`, `.email`, `.name`); `None` for a legacy
  key with no bound user.

## [0.15.0]

### Added
- `attendance.summary(from_=..., to=...)` for `GET /api/v1/attendance/summary` (Attendance Summary):
  company-wide, one row per employee with the consolidated totals over the range (`worked_minutes`,
  `expected_minutes`, `balance_minutes`, `worked_days`, `expected_days`). Optional `status`,
  `department_id`, `work_center_id` filters and `tz`; paginated over employees. Returns a new
  `AttendanceSummaryPage` of `AttendanceSummary` models.

## [0.14.0]

### Added
- `me()` for `GET /api/v1/me` (Whoami): returns the tenant the key belongs to and its enabled scopes.
  Not scope-gated — a good first call to verify a key works. Returns a new `Identity` model (`.tenant`,
  `.scopes`).

## [0.13.0]

### Added
- `holidays.list(work_center_id, year=None)` for `GET /api/v1/holidays` (List Holidays): the festivo
  calendar of one work center — each holiday a `date`, `name` and `type` (national/regional/local).
  Optional `year` filter, paginated. Returns a new `HolidayPage` of `Holiday` models.

## [0.12.0]

### Added
- `absence_types.list()` for `GET /api/v1/absence-types` (List Absence Types): the company's absence-type
  catalogue — the `key` that `Absence.type` references plus its attributes (`paid`, `consumes_vacation`,
  `requires_approval`, `requires_justification`, `allows_hourly`, `day_count_mode`, `active`). Returns a
  new `AbsenceTypePage` of `AbsenceType` models. `AbsenceType` gained those attribute fields (still
  populated only with `key`/`label` when nested inside an `Absence`).

## [0.11.0]

### Added
- `users.list(email=...)` — exact, case-insensitive email filter on `GET /api/v1/users`. Resolves an
  external identity (the email your system holds) to our user id; returns at most one result. Unlike `q`
  (a substring search over name+email), `email` is an exact match.

## [0.10.0]

### Added
- `expenses.get(expense_id)` for `GET /api/v1/expenses/:expense_id` (Get Expense): a single expense by
  id, with its OCR money fields, category, status and `reconciled` flag. Returns the existing `Expense`
  model. Raises `NotFoundError` for an unknown or cross-company id.

## [0.9.0]

### Added
- `expenses.list()` for `GET /api/v1/expenses` (List Expenses): the company's expense receipts (Mis
  Gastos), newest first, with the OCR-extracted money fields (`total_amount`, `tax_amount`, `currency`,
  `amount_eur`, `fx_rate`), `category`, `status` and `reconciled`. Optional `user_id`/`status` filters,
  paginated. Returns a new `ExpensePage` model (`.items`, `.page`, `.page_size`, `.total`; iterable and
  `len()`-able) holding `Expense` models.

## [0.8.0]

### Added
- `absences.get(absence_id)` for `GET /api/v1/absences/:absence_id` (Get Absence): a single absence by
  id, with its type (key + label), status, dates and — for hourly absences — the time slice. Returns the
  existing `Absence` model. Raises `NotFoundError` for an unknown or cross-company id.

## [0.7.0]

### Added
- `work_centers.list()` for `GET /api/v1/work-centers` (List Work Centers): the company's work centers
  (sedes), alphabetical, each with its location — `country` plus `region`/`province`/`municipality`, each
  a `GeoRef` ({code, name}) or `None`. Paginated (`page`/`page_size`). Returns a new `WorkCenterPage` model
  (`.items`, `.page`, `.page_size`, `.total`; iterable and `len()`-able) holding `WorkCenter` and `GeoRef`
  models.

## [0.6.0]

### Added
- `departments.list()` for `GET /api/v1/departments` (List Departments): the company's departments,
  alphabetical, each with its `employee_count` and its `supervisor` department (the org tree; `None` at
  the root). Paginated (`page`/`page_size`). Returns a new `DepartmentPage` model (`.items`, `.page`,
  `.page_size`, `.total`; iterable and `len()`-able) holding `Department` models.

## [0.5.0]

### Added
- `absences.list(from_=..., to=...)` for `GET /api/v1/absences` (List Absences): every absence that
  overlaps the range (both ends inclusive), newest first, with optional `user_id`, `status` and `type`
  filters. Returns a new `AbsencePage` model (`.items`, `.page`, `.page_size`, `.total`; iterable and
  `len()`-able) holding `Absence` and `AbsenceType` models. Hourly absences carry `start_time`/`end_time`;
  whole-day ones leave them `None`.

## [0.4.0]

### Added
- `attendance.list(user_id, from_=..., to=...)` for `GET /api/v1/attendance` (List Attendance): one entry
  per calendar day of the range (both ends inclusive), with the day's marks, the minutes actually worked
  (pauses already discounted) and the balance against the employee's schedule. Optional `tz` (defaults to
  `Europe/Madrid` server-side), `page` and `page_size`. Returns a new `AttendancePage` model (`.items`,
  `.page`, `.page_size`, `.total`; iterable and `len()`-able) holding `AttendanceDay` and `Punch` models.
  Note the trailing underscore in `from_`: `from` is a reserved word in Python.

## [0.3.0]

### Added
- `users.list(...)` for `GET /api/v1/users` (List Users): paginated (`page`, `page_size`), with filters
  `status`, `role`, `department_id`, `work_center_id`, `q`, and `detail="reduced"|"full"`. Returns a new
  `UserPage` model (`.items`, `.page`, `.page_size`, `.total`; iterable and `len()`-able).

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
