from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import sqlite3, time

app = FastAPI()

DB = "inspector.db"

STATIONS = [
    {"id": 1, "name": "תחנה מרכזית ראשון לציון",     "lat": 31.9730, "lon": 34.7895},
    {"id": 2, "name": "בית החולים קפלן",               "lat": 31.9642, "lon": 34.7817},
    {"id": 3, "name": "רכבת ראשון לציון משה דיין",     "lat": 31.9884, "lon": 34.7763},
    {"id": 4, "name": "רכבת ראשון לציון הראשונים",     "lat": 31.9613, "lon": 34.8012},
    {"id": 5, "name": "קניון הזהב",                    "lat": 31.9748, "lon": 34.8031},
    {"id": 6, "name": "מרכז קליטה / אגמים",            "lat": 31.9801, "lon": 34.7712},
    {"id": 7, "name": "בית ברל / וולפסון",             "lat": 31.9553, "lon": 34.7934},
    {"id": 8, "name": "שדרות רוטשילד / הרצל",          "lat": 31.9677, "lon": 34.8056},
]

WINDOW_SECONDS = 5 * 60  # 5 minutes

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    # Drop old table if it has the old schema (single row per station)
    conn.execute("DROP TABLE IF EXISTS reports")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            station_id INTEGER NOT NULL,
            has_inspector INTEGER NOT NULL,
            reported_at REAL NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

class Report(BaseModel):
    station_id: int
    has_inspector: bool

@app.get("/", response_class=HTMLResponse)
def root():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/stations")
def get_stations():
    conn = get_db()
    now = time.time()
    cutoff = now - WINDOW_SECONDS

    # Get all reports in last 5 minutes
    rows = conn.execute(
        "SELECT station_id, has_inspector FROM reports WHERE reported_at >= ?",
        (cutoff,)
    ).fetchall()
    conn.close()

    # Count yes/no votes per station
    votes = {}
    for row in rows:
        sid = row["station_id"]
        if sid not in votes:
            votes[sid] = {"yes": 0, "no": 0}
        if row["has_inspector"]:
            votes[sid]["yes"] += 1
        else:
            votes[sid]["no"] += 1

    result = []
    for s in STATIONS:
        v = votes.get(s["id"])
        if v:
            has_inspector = v["yes"] > v["no"]
            total = v["yes"] + v["no"]
        else:
            has_inspector = None
            total = 0
        result.append({
            **s,
            "has_inspector": has_inspector,
            "yes_votes": v["yes"] if v else 0,
            "no_votes": v["no"] if v else 0,
            "total_votes": total,
        })
    return result

@app.post("/report")
def post_report(report: Report):
    conn = get_db()
    conn.execute(
        "INSERT INTO reports (station_id, has_inspector, reported_at) VALUES (?, ?, ?)",
        (report.station_id, int(report.has_inspector), time.time())
    )
    conn.commit()
    conn.close()
    return {"ok": True}
