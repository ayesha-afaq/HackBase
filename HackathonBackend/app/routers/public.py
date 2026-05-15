
from fastapi import APIRouter
from app.database import get_connection

router = APIRouter(prefix='/public', tags=['Public'])


# ── View all events (no login required) ─────────────────────────────
@router.get('/events')
def public_events():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT event_id, event_name, start_date, end_date,
               event_status, event_details
        FROM HackathonEvents
        ORDER BY start_date DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "event_id": r.event_id,
            "event_name": r.event_name,
            "start_date": str(r.start_date),
            "end_date": str(r.end_date),
            "status": r.event_status,
            "details": r.event_details
        }
        for r in rows
    ]


# ── Event Results + Ranking ─────────────────────────────
@router.get('/event-results/{event_id}')
def event_results(event_id: int):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            t.team_name,
            AVG(e.score) AS avg_score,
            COUNT(e.evaluation_id) AS total_evals
        FROM Teams t
        INNER JOIN Projects p ON t.team_id = p.team_id
        INNER JOIN Evaluations e ON p.project_id = e.project_id
        WHERE t.event_id = ?
        GROUP BY t.team_name
        ORDER BY avg_score DESC
    """, (event_id,))

    rows = cursor.fetchall()
    conn.close()

    ranked = []
    rank = 1

    for r in rows:
        ranked.append({
            "rank": rank,
            "team_name": r.team_name,
            "average_score": float(r.avg_score),
            "evaluations": r.total_evals
        })
        rank += 1

    return ranked