# dutybeat (Python)

Official Python client for the [DutyBeat](https://dutybeat.com) public API.

## Install

```bash
pip install dutybeat
```

## Usage

```python
from dutybeat import DutyBeat

client = DutyBeat(api_key="db_live_...")          # or set DUTYBEAT_API_KEY
user = client.users.get("9f1c...", include_folders=True)

print(user.full_name, user.email)
print(user.department.name)
print(user.profile.iban)
for folder in user.folders or []:
    print(folder.name, folder.document_count)

# List users (paginated, filterable)
page = client.users.list(page_size=50, status="active", role="member")
for u in page:                       # UserPage is iterable
    print(u.full_name, u.email)
print("total:", page.total)

# List an employee's workdays (marks, worked minutes, balance). `from_` because `from` is reserved.
days = client.attendance.list("9f1c...", from_="2026-06-01", to="2026-06-30")
for day in days:                     # AttendancePage is iterable
    print(day.date, day.worked_minutes, day.balance_minutes)

# List absences overlapping a range (whole company, or one employee with user_id=...)
for absence in client.absences.list(from_="2026-06-01", to="2026-06-30", status="approved"):
    print(absence.start_date, absence.end_date, absence.type.label)
```

Create an API key in the app under **Configuración → Claves de API**, and enable the methods each key
may call. Full reference: **Configuración → API** (or `https://app.dutybeat.com/configuracion/api`).

### Errors

```python
from dutybeat import DutyBeat, AuthenticationError, ForbiddenError, NotFoundError, RateLimitError

try:
    client.users.get("9f1c...")
except NotFoundError:
    ...          # 404
except ForbiddenError:
    ...          # 403 — the key does not have this method enabled
except AuthenticationError:
    ...          # 401 — bad / revoked / expired key
except RateLimitError as e:
    print(e.retry_after)   # 429
```

Every error exposes `.status`, `.code` and `.message` from the API's error envelope.

## Configuration

| Argument | Default | |
|---|---|---|
| `api_key` | `DUTYBEAT_API_KEY` env | Your `db_live_...` key |
| `base_url` | `https://api.dutybeat.com` | Override for testing |
| `timeout` | `30.0` | Seconds |
| `max_retries` | `2` | Retries on `429`/`5xx`, honouring `Retry-After` |

## Development

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT
