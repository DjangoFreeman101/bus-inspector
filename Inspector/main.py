import csv as csv_module
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg2, psycopg2.extras, time, os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def load_stations():
    stations = []
    with open("stations.csv", encoding="utf-8") as f:
        reader = csv_module.DictReader(f)
        for row in reader:
            stations.append({
                "id": int(row["stop_code"]),
                "name": row["stop_name"],
                "lat": float(row["stop_lat"]),
                "lon": float(row["stop_lon"])
            })
    return stations

STATIONS = load_stations()

WINDOW_SECONDS = 5 * 60  # 5 minutes

def get_db():
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            user_id TEXT NOT NULL,
            station_id INTEGER NOT NULL,
            has_inspector BOOLEAN NOT NULL,
            reported_at DOUBLE PRECISION NOT NULL,
            PRIMARY KEY (user_id, station_id)
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

init_db()

class Report(BaseModel):
    station_id: int
    has_inspector: bool
    user_id: str

@app.get("/", response_class=HTMLResponse)
def root():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/manifest.json")
def manifest():
    return FileResponse("manifest.json", media_type="application/manifest+json")

@app.get("/icon.png")
def icon():
    return FileResponse("icon.png", media_type="image/png")

@app.get("/sw.js")
def service_worker():
    return FileResponse("sw.js", media_type="application/javascript")

@app.get("/privacy")
def privacy():
    return FileResponse("privacy_policy.html", media_type="text/html")

@app.get("/search")
def search_stations(q: str = ""):
    if not q or len(q) < 1:
        return []
    q_lower = q.strip()
    results = [
        s for s in STATIONS
        if q_lower in s["name"] or q_lower in str(s["id"])
    ]
    return results[:30]

@app.get("/stations")
def get_stations(
    lat_min: float = None,
    lat_max: float = None,
    lon_min: float = None,
    lon_max: float = None
):
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    now = time.time()
    cutoff = now - WINDOW_SECONDS

    # Get all reports in last 5 minutes
    cur.execute(
        "SELECT station_id, has_inspector FROM reports WHERE reported_at >= %s",
        (cutoff,)
    )
    rows = cur.fetchall()

    # Get last inspector report time per station (all time)
    cur.execute(
        "SELECT station_id, MAX(reported_at) as last_seen FROM reports WHERE has_inspector = true GROUP BY station_id"
    )
    last_seen_rows = cur.fetchall()
    last_seen = {row["station_id"]: row["last_seen"] for row in last_seen_rows}

    cur.close()
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

    # Filter stations by bounding box if provided
    stations = STATIONS
    if lat_min is not None and lat_max is not None and lon_min is not None and lon_max is not None:
        stations = [s for s in STATIONS if lat_min <= s["lat"] <= lat_max and lon_min <= s["lon"] <= lon_max]

    result = []
    for s in stations:
        v = votes.get(s["id"])
        if v:
            has_inspector = v["yes"] > v["no"]
            total = v["yes"] + v["no"]
        else:
            has_inspector = None
            total = 0
        last_ts = last_seen.get(s["id"])
        result.append({
            **s,
            "has_inspector": has_inspector,
            "yes_votes": v["yes"] if v else 0,
            "no_votes": v["no"] if v else 0,
            "total_votes": total,
            "last_inspector_time": last_ts,
            "danger_level": None,  # populated later from historical data
        })
    return result

@app.delete("/report")
def delete_report(station_id: int, user_id: str):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM reports WHERE user_id = %s AND station_id = %s",
        (user_id, station_id)
    )
    conn.commit()
    cur.close()
    conn.close()
    return {"ok": True}

@app.post("/report")
def post_report(report: Report):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO reports (user_id, station_id, has_inspector, reported_at)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT(user_id, station_id) DO UPDATE SET
            has_inspector = EXCLUDED.has_inspector,
            reported_at = EXCLUDED.reported_at
    """, (report.user_id, report.station_id, report.has_inspector, time.time()))
    conn.commit()
    cur.close()
    conn.close()
    return {"ok": True}
