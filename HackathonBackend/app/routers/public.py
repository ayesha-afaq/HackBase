from fastapi import APIRouter, HTTPException
from app.database import get_connection

router = APIRouter(prefix='/public', tags=['Public'])


# ── View all events (no login required) ─────────────────────────────
@router.get('/events')
def public_events():

    conn = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT event_id, event_name, start_date, end_date,
                   event_status, event_details
            FROM HackathonEvents
            ORDER BY start_date DESC
        """)

        rows = cursor.fetchall()

        if not rows:
            raise HTTPException(
                status_code=404,
                detail="No events found"
            )

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

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching events: {str(e)}"
        )

    finally:
        if conn:
            conn.close()


# ── Event Results + Ranking ─────────────────────────────
@router.get('/event-results/{event_id}')
def event_results(event_id: int):

    conn = None

    try:
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

        if not rows:
            raise HTTPException(
                status_code=404,
                detail=f"No results found for event_id {event_id}"
            )

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

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching event results: {str(e)}"
        )

    finally:
        if conn:
            conn.close()