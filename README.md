# Pipeline Readings Viewer

A small full-stack app for reviewing one inspection run of an oil pipeline. A robot
records pressure and temperature every few metres; the app loads such a run, flags the
readings that deviate from the local pressure trend, and shows them to an engineer.

- **Backend** — Django 5 + Django REST Framework, SQLite
- **Frontend** — Vue 3 + TypeScript + Vite, Tailwind CSS v4, Headless UI, Chart.js, axios
- **Data** — any CSV with the columns `distance_m`, `pressure_bar`, `temperature_c`

The repository ships a Django fixture of the assignment's 400-reading sample. In
**development** (the default) it is loaded when the server process starts, so the app
opens with data. Set `DJANGO_ENV=production` to skip that and start empty. Uploading a
CSV replaces whatever run is loaded.

---

## Running it

### Docker

```bash
docker compose up --build
```

Then open <http://localhost:5173>. The API is at <http://localhost:8000>, with Swagger at
<http://localhost:8000/docs/>. Development is the default, so the sample fixture loads
when the backend container starts.

### Without Docker

You need **Python 3.10+** and **Node 18+**. Two terminals, backend first.

### 1. Backend (http://127.0.0.1:8000)

```bash
cd backend
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
python manage.py migrate
python manage.py runserver          # DJANGO_ENV defaults to dev; loads the sample fixture
```

Swagger UI is at <http://127.0.0.1:8000/docs/>, ReDoc at <http://127.0.0.1:8000/redoc/>,
and the OpenAPI schema at <http://127.0.0.1:8000/schema/>.

To start without the sample run:

```bash
# Windows PowerShell
$env:DJANGO_ENV = "production"
python manage.py runserver
# macOS / Linux
DJANGO_ENV=production python manage.py runserver
```

### 2. Frontend (http://127.0.0.1:5173)

```bash
cd frontend
npm install
npm run dev
```

Open <http://127.0.0.1:5173>. If your backend is not on `http://127.0.0.1:8000`, set
`VITE_API_BASE` (for example in `frontend/.env.local`) to point at it.

### Loading a run

In development the bundled `sample_run` fixture is loaded on process start (WSGI/ASGI),
so a fresh `runserver` already has the 400-reading sample. Production (`DJANGO_ENV=production`)
does not load it. Either way of getting data into a running app:

- **Upload it in the UI** — any CSV with the columns `distance_m`, `pressure_bar`,
  `temperature_c`. This replaces the current run.
- **Reload the sample** — `python manage.py load_sample` replaces the current run with
  the fixture.

### Tests and checks

```bash
cd backend
python manage.py test          # 80 tests
```

```bash
cd frontend
npm run typecheck              # vue-tsc, no emit
npm run lint                   # eslint, flat config
npm run format:check           # prettier
```

ESLint runs `eslint-plugin-vue`'s `flat/recommended` (the Vue style guide's
strongly-recommended tier, not just the essential one) together with
`typescript-eslint`; Prettier owns formatting, so the two do not argue. `npm run lint:fix`
and `npm run format` apply what they can.

---

## API

All responses are JSON. Errors always have the shape `{"detail": "<readable message>"}`,
so the frontend has exactly one place to look for something to show the user.

| Method | Path        | Description |
|---|---|---|
| `GET`  | `/`         | Lists the endpoints, so the root is not a 404 in a browser. |
| `POST` | `/upload`   | Replaces the current run. `multipart/form-data`, field name `file`. |
| `GET`  | `/readings` | Readings of the current run. Optional `from_m` / `to_m`. |
| `GET`  | `/summary`  | Min / max / mean pressure, reading count, anomaly count. Same filters. |
| `GET`  | `/docs`     | Swagger UI. |
| `GET`  | `/redoc`    | ReDoc. |
| `GET`  | `/schema`   | OpenAPI 3 schema (YAML). |

`from_m` and `to_m` are inclusive bounds in metres and may be given independently.

```bash
curl -F "file=@/path/to/sensor_readings.csv" http://127.0.0.1:8000/upload
curl "http://127.0.0.1:8000/readings?from_m=480&to_m=500"
curl "http://127.0.0.1:8000/summary?from_m=1200&to_m=1240"
```

A reading looks like this:

```json
{
  "distance_m": 1200,
  "pressure_bar": 46.5,
  "temperature_c": 18.3,
  "anomaly": true,
  "baseline_mean": 41.046,
  "baseline_std": 0.3102698316321657
}
```

`baseline_mean` / `baseline_std` are the local trend the reading was judged against.
They are not required by the brief, but they let the UI show *how far* off a reading is
(in σ) instead of only *that* it is off, and they make the rule auditable from the API
alone. They are `null` for the first two readings of a run, where no standard deviation
can be estimated.

Both read endpoints also return the run itself, including `distance_range` — the run's
full extent, unaffected by the filter. The UI needs it to offer range presets and input
hints for an arbitrary uploaded file, which it cannot infer from a filtered slice.

### Validation

A malformed upload returns `400` with a specific message and **leaves the currently
loaded run untouched** — parsing fully succeeds before anything is written. Rejected
cases include: empty file, header with no data rows, missing or misspelled columns,
non-numeric or blank values, `NaN`/`inf`, rows shorter than the header, duplicate
distances, fractional distances, non-UTF-8 binary files, and files over 10 MB. Unknown
extra columns are ignored, a UTF-8 BOM is handled, and rows that arrive out of order are
sorted by distance.

---

## The anomaly rule

A reading is flagged when its pressure deviates from the local trend by more than two
standard deviations:

```
anomaly(i)  ⇔  |p(i) − μ(i)| > 2 · σ(i)
```

where μ(i) and σ(i) are the mean and standard deviation of the **20 readings preceding
i** — a shorter window near the start of the run. The implementation
([`backend/readings/anomaly.py`](backend/readings/anomaly.py)) is a direct transcription
of that formula using the standard library's `statistics` module.

Three decisions the formula leaves open:

- **σ is the sample (Bessel-corrected, n−1) standard deviation.** The window is a sample
  used to estimate the local spread, so n−1 is the appropriate estimator. On a 20-reading
  window the difference from the population form is under 3% and changes no flags in the
  sample data.
- **The first two readings are never flagged.** A standard deviation needs at least two
  data points, so their baseline is reported as `null` rather than guessed at.
- **A zero-variance window degenerates to `p ≠ μ`.** This is the literal reading of the
  rule and cannot divide by zero. A perfectly flat run therefore produces no anomalies at
  all, which is the intuitive answer.

### What this rule does and does not catch

Worth knowing before trusting the output — on the sample run it flags **39 of 400
readings**:

- **It reliably catches the onset of an event.** The leak-like drop at **480–500 m**
  (≈43.5 → 39 bar) is flagged on all five readings.
- **It under-reports sustained events.** The pump-station-like jump at **1200–1240 m**
  (≈41 → 47 bar) spans nine readings but only the **first five** are flagged. By 1225 m
  the trailing window has absorbed the jump — σ inflates from 0.31 to over 2.5 — so the
  remaining elevated readings fall back inside the 2σ band. The return to normal at
  1245 m is masked the same way. This is inherent to a trailing window that adapts to
  recent history, not a bug in the implementation, and
  `test_sustained_jump_is_only_flagged_at_its_onset` pins the behaviour down.
- **It produces false positives by construction.** A 2σ threshold flags roughly 5% of
  normally distributed readings, so about 20 of the 39 flags on the sample run are
  ordinary scatter rather than physical events — the isolated single-reading flags at
  150 m, 920 m or 1460 m, for instance. This is why the UI groups flags into contiguous
  segments: a five-reading segment is a event, a lone flag usually is not.

I implemented the rule exactly as specified rather than silently substituting something
more robust; the alternatives I would reach for are in
[Next steps](#if-this-went-to-production).

---

## Key decisions

**Framework.** Django + DRF over FastAPI. The domain is small but genuinely relational
(a run owns its readings), so the ORM, migrations and the `manage.py` entry point for the
seeding command pay for the extra ceremony. SQLite needs no setup and survives a restart,
which in-memory storage would not.

**The sample run is a Django fixture, loaded only in development.** `DJANGO_ENV`
defaults to `dev`, and the WSGI/ASGI process loads `sample_run.json` if the database
is empty. Production (`DJANGO_ENV=production`) skips it, so a deployed app starts
blank. That replaces request-time middleware, which mixed HTTP handling with
seeding.

**Each layer has one job.** Query logic lives on a custom `ReadingQuerySet`
(`in_distance_range`, `anomalous`, `pressure_stats`) and writes on a `RunManager`
(`current`, `replace`), so the views never assemble filters or aggregates by hand and
the same vocabulary is reusable from the shell or a management command. Distance
filters (`from_m` / `to_m`) are a django-filter `FilterSet` that calls
`in_distance_range`; uploads are validated by a serializer. The read endpoints are
DRF generic views (`ListAPIView`, `GenericAPIView`) over the current run's `Reading`
queryset; upload is a `CreateAPIView`.
Views raise domain exceptions (`InvalidReadingsFile`, `NoRunLoaded`) and a custom DRF exception
handler renders every error — including field-level validation errors DRF would
otherwise shape as `{"from_m": [...]}` — as a single `{"detail": "..."}`. That is what
lets the frontend have exactly one error path.

**Anomaly flags are computed once, at upload time, over the whole run** and stored on each
reading. The alternative — computing per request — would make a reading's verdict depend
on the distance filter in effect: filtering to `from_m=1200&to_m=1200` would leave the
window empty and report the biggest anomaly in the run as normal. Flags describe the
reading, not the query, so they are computed where the data is complete.
`test_flag_survives_a_filter_that_hides_the_baseline` guards this.

**Statistics use the standard library**, not numpy or pandas. At 400 readings per run a
dependency that large buys nothing, and a plain loop maps one-to-one onto the formula in
the brief, which matters more for a rule someone has to trust.

**Data flow.** The frontend holds no derived state: the distance filter is sent to the API
and both `/readings` and `/summary` are re-fetched in parallel, so the chart and the
summary numbers can never disagree. Filtering is server-side, as specified. The only
client-side computation is presentational — grouping adjacent flagged readings into
segments and converting a deviation into σ for display. That pairing lives in one
composable, `useRun`, rather than in the component, so nothing can fetch readings without
the matching summary and `App.vue` is left holding only layout and view state.

**One error path on the client too.** `api.ts` is a single configured axios instance with
a response interceptor that turns anything axios throws into an `ApiError` carrying a
message fit to show the user: the backend's `detail` when there is a response body, and
"is the Django server running?" when there is no response at all. Components therefore
catch one error type and never touch HTTP status codes, apart from asking
`error.isNoRunLoaded` to tell "nothing uploaded yet" apart from a real failure.

**Frontend shows a chart *and* a table.** The chart answers "where should I look" — the
pressure profile with anomalies as red dots, plus an optional dashed overlay of the local
baseline, which makes the masking behaviour above visible. The segment table answers
"what did it find", naming each stretch, its direction (drop vs jump) and its peak
deviation. An engineer scanning for problems wants both, so the chart stays permanently
visible and the tabular detail sits behind tabs (segments / all readings).

**Styling is Tailwind CSS v4, with a small shared component layer.** The feature
components carry no CSS of their own: everything is composed from `src/components/ui`
(`Button`, `Card`, `Table`, `Stat`, `Badge`, `Alert`, `Input`, `Switch`, `Select`,
`Tabs`, `Modal`), imported through a barrel so call sites read
`import { Card, Table } from './components/ui'`. That keeps spacing, colour and focus
states defined once, and it means `AnomalySegments` and `ReadingsTable` are just a
column definition plus a couple of cell slots over the same `Table`. The interactive
primitives — toggle, dropdown, tabs, modal — wrap **Headless UI**, so keyboard
navigation, focus trapping and ARIA wiring are handled properly rather than
reimplemented on `div`s.

---

## Project structure

```
docker-compose.yml
backend/
  Dockerfile
  pipeline/            Django project: settings, urls, wsgi/asgi
  readings/
    anomaly.py         the statistical rule
    csv_import.py      parsing and validation of uploads
    models.py          Run / Reading, ReadingQuerySet, RunManager
    filters.py         FilterSet for the from_m / to_m distance window
    serializers.py     ModelSerializers and upload validation
    views.py           CreateAPIView / ListAPIView / GenericAPIView
    exceptions.py      domain errors and the {"detail": ...} handler
    sample.py          loads the sample fixture on process start in dev
    fixtures/
      sample_run.json  the assignment's 400-reading sample, flags included
    tests/             80 tests
frontend/
  Dockerfile
  eslint.config.js     flat config: vue + typescript + prettier
  .prettierrc.json     formatting, incl. Tailwind class sorting
  src/
    api.ts             typed axios client, one error shape
    segments.ts        grouping flags into segments for display
    composables/
      useRun.ts        the loaded run: fetching, filtering, replacing
    App.vue            layout and view state only
    components/
      ui/              shared kit: Button, Card, Table, Tabs, Modal, ...
      PressureChart.vue, AnomalySegments.vue, ReadingsTable.vue,
      SummaryPanel.vue, UploadControl.vue, DistanceFilter.vue
```

---

## If this went to production

- **Make the detector robust.** Use a median and MAD instead of mean and standard
  deviation so a large excursion cannot inflate the very baseline it is measured against,
  and compare each reading against a *centred* or two-sided window so sustained shifts do
  not mask their own tails. Add hysteresis so an event closes only after pressure returns
  to the baseline, which would catch the full 1200–1240 m plateau as one event.
- **Detect at the segment level, not the reading level.** Engineers act on segments, and a
  minimum-length requirement would remove most of the ~20 single-reading false positives
  at almost no cost in sensitivity. Pressure gradient (bar per metre) is also more
  physical than absolute pressure for locating a leak.
- **Make the rule configurable and versioned**, so window size and threshold can be tuned
  per pipeline section and a stored flag can be traced to the parameters that produced it.
- **Keep run history** rather than replacing a single run, so a run can be compared with
  earlier passes over the same section — far stronger evidence than any single-run
  statistic. This is a migration plus dropping the `Run.replace` semantics.
- **Handle real file sizes.** Parse and detect in a background worker with progress
  reporting, stream the CSV instead of holding it in memory, and paginate or downsample
  `/readings` — a 100 km run at 5 m spacing is 20,000 points, more than a browser chart
  wants at once.
- **Operational basics**: authentication and per-user run ownership, structured logging,
  CI running the test suite plus linting (`ruff`, `eslint`), pinned lockfiles, and
  locking the OpenAPI schema into the frontend client.

## Known gaps

Deliberate scope cuts, given that the exercise asks for thinking rather than polish:

- **No frontend tests.** The backend has 80 tests covering the anomaly math, every
  validation path, the query layer and the API contract, which is where the logic worth
  protecting lives. The frontend is typechecked and linted but has no unit tests; it
  would need Vitest plus a component harness, and `segments.ts` is the piece I would
  test first.
- **The backend has no linter configured.** The frontend runs ESLint and Prettier;
  `ruff` for Python would be the obvious counterpart and is not set up.
- **The UI kit uses single-word component names** (`Button`, `Table`), which the Vue
  style guide advises against because they can collide with HTML elements. The rule is
  switched off for `src/components/ui/*.vue` only, with the reasoning recorded in
  `eslint.config.js`: these are imported explicitly rather than globally registered, so
  the collision the rule guards against cannot happen here, and the shorter names read
  better at the call site.
- **The UI aims at clarity rather than polish**, as the brief allows. It reflows down to
  a narrow window but has not been designed for mobile, and the chart is not zoomable —
  the distance filter is the way to look closely at a segment.
- **The original assignment CSV is git-ignored**, together with the brief and
  `db.sqlite3`. The sample is published as a Django fixture (`sample_run.json`) so a
  clone in development can start with data without committing the file you sent. Every
  anomaly figure quoted above comes from that sample.

## AI tool usage

Built with **Cursor** (Claude). I used it for:

- Scaffolding the Django project and Vue components, and writing the repetitive parts —
  serializers, the Tailwind class lists in the shared UI components, and the test
  fixtures for each malformed-CSV case.
- Exploring the sample data before designing anything: throwaway scripts that ran the
  brief's formula over `sensor_readings.csv` and printed the baseline μ and σ around each
  cluster of flags. That is how the 1200 m masking behaviour and the false-positive rate
  documented above were found, and it changed what I chose to store and display.
- Drafting this README, which I then edited for accuracy.

The architectural decisions — computing flags at write time, storing the baseline,
implementing the rule literally and documenting its limits rather than "improving" it,
and grouping segments in the view layer — are mine, and I reviewed every line. I am happy
to walk through and modify any part of it on a call.

## Time spent

8h
