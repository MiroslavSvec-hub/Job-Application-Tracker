# Job Application Tracker

A small local app for tracking job applications. All data is stored in a
plain CSV file (`applications.csv`) in this folder — no browser storage,
no external database. You can open that CSV directly in Excel/Numbers/Sheets
at any time if you want to look at or back up the raw data.

## Features

- Add, edit and delete applications
- Status tracking (Applied, Screening, Interview, Offer, Rejected, Withdrawn)
  with colour-coded cards and badges
- **Match quality** (Low / Medium / Strong) shown as a coloured badge, so
  strong matches stand out at a glance
- **Reason for match quality** — a short note on why a role is or isn't a fit
- Summary counts per status, filter by status, search by company or role
- "Applied X days ago" indicator that turns orange after 2 weeks and red
  after a month

## Setup

1. Make sure you have Python 3 installed.
2. Install the one dependency (Flask):

   ```
   pip install -r requirements.txt
   ```

## Run

```
python app.py
```

Then open **http://127.0.0.1:5000** in your browser.

## How it works

- The page (HTML/CSS/JS) is served by a small Flask app.
- Adding, editing, or deleting an application sends a request to the Flask
  server, which reads/writes `applications.csv` directly.
- `applications.csv` is created automatically the first time you save an
  application — you don't need to create it yourself.
- Stopping the server (Ctrl+C) doesn't lose any data — everything is
  already saved to the CSV file as you go.
- `applications.csv` is listed in `.gitignore`, so your personal data is
  never committed to the repository.

## CSV columns

| Column         | Description                                                        |
| -------------- | ------------------------------------------------------------------ |
| `id`           | Generated automatically                                            |
| `company`      | Required                                                           |
| `role`         | Required                                                           |
| `dateApplied`  | `YYYY-MM-DD`                                                       |
| `status`       | `applied`, `screening`, `interview`, `offer`, `rejected`, `withdrawn` |
| `matchQuality` | Optional: `low`, `medium`, `strong` (labels like `Strong match` also work) |
| `matchReason`  | Optional free text                                                 |
| `salary`       | Free text, e.g. `£60k–£65k`                                        |
| `link`         | Job posting URL                                                    |
| `notes`        | Notes / next action                                                |

## Files

```
job_tracker/
├── app.py              Flask server + CSV read/write logic
├── requirements.txt
├── applications.csv    Created automatically on first save (git-ignored)
├── templates/
│   └── index.html
└── static/
    ├── style.css
    └── app.js
```
