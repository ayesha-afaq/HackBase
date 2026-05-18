from fastapi import APIRouter, HTTPException, Request, Depends
from app.database import get_connection
from app.routers.auth import verify_token
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix='/judge', tags=['Judge'])


# ── REQUEST MODELS ────────────────────────────────────────────────
class EvaluateRequest(BaseModel):
    project_id: int
    score     : float
    feedback  : Optional[str] = None

class UpdateFeedbackRequest(BaseModel):
    project_id: int
    feedback  : str


# ── HELPER ────────────────────────────────────────────────────────────────────
def get_judge_id(user_id, cursor):
    cursor.execute(
        "SELECT judge_id FROM Judges WHERE user_id = ?",
        (user_id,)
    )
    row = cursor.fetchone()

    if not row:
        raise HTTPException(status_code=403, detail="Not a judge account")

    return row.judge_id


# ── 1. View ALL projects assigned to this judge ───────────────────────────────
@router.get('/assigned-projects')
def assigned_projects(user = Depends(verify_token)):
    """
    Returns every project in every event this judge is assigned to.
    The 'already_evaluated' flag tells the frontend which ones are done.
    Also returns the judge's own score/feedback if they already evaluated.
    Pending projects appear first (already_evaluated ASC).
    """
    conn   = get_connection()
    cursor = conn.cursor()

    try:
        judge_id = get_judge_id(user["user_id"], cursor)

        cursor.execute(
            '''
            SELECT
                p.project_id,
                p.project_name,
                p.status,
                p.github_link,
                p.description,
                p.submission_date,
                t.team_name,
                t.team_id,
                he.event_name,
                he.event_id,
                CASE WHEN e.evaluation_id IS NOT NULL THEN 1 ELSE 0 END AS already_evaluated,
                e.score    AS my_score,
                e.feedback AS my_feedback
            FROM Projects p
            INNER JOIN Teams           t   ON p.team_id   = t.team_id
            INNER JOIN HackathonEvents he  ON t.event_id  = he.event_id
            INNER JOIN EventJudges     ej  ON he.event_id = ej.event_id
                                          AND ej.judge_id = ?
            LEFT  JOIN Evaluations     e   ON e.project_id = p.project_id
                                          AND e.judge_id   = ?
            ORDER BY already_evaluated ASC, p.project_id ASC
            ''',
            (judge_id, judge_id)
        )
        rows = cursor.fetchall()

        return [
            {
                'project_id'       : r.project_id,
                'project_name'     : r.project_name,
                'status'           : r.status,
                'github_link'      : r.github_link,
                'description'      : r.description,
                'submission_date'  : str(r.submission_date),
                'team_name'        : r.team_name,
                'team_id'          : r.team_id,
                'event_name'       : r.event_name,
                'event_id'         : r.event_id,
                'already_evaluated': bool(r.already_evaluated),
                'my_score'         : float(r.my_score)  if r.my_score    is not None else None,
                'my_feedback'      : r.my_feedback       if r.my_feedback is not None else None,
            }
            for r in rows
        ]

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        conn.close()


# ── 2. View ONLY pending (not yet evaluated) projects ─────────────────────────
@router.get('/pending-projects')
def pending_projects(user = Depends(verify_token)):
    """
    Returns only the projects this judge has NOT evaluated yet.
    """
    conn   = get_connection()
    cursor = conn.cursor()

    try:
        judge_id = get_judge_id(user["user_id"], cursor)

        cursor.execute(
            '''
            SELECT
                p.project_id,
                p.project_name,
                p.github_link,
                p.submission_date,
                t.team_name,
                he.event_name,
                he.event_id
            FROM Projects p
            INNER JOIN Teams           t   ON p.team_id   = t.team_id
            INNER JOIN HackathonEvents he  ON t.event_id  = he.event_id
            INNER JOIN EventJudges     ej  ON he.event_id = ej.event_id
                                          AND ej.judge_id = ?
            WHERE NOT EXISTS (
                SELECT 1 FROM Evaluations e
                WHERE e.project_id = p.project_id
                  AND e.judge_id   = ?
            )
            ORDER BY p.submission_date ASC
            ''',
            (judge_id, judge_id)
        )
        rows = cursor.fetchall()

        return [
            {
                'project_id'     : r.project_id,
                'project_name'   : r.project_name,
                'github_link'    : r.github_link,
                'submission_date': str(r.submission_date),
                'team_name'      : r.team_name,
                'event_name'     : r.event_name,
                'event_id'       : r.event_id,
            }
            for r in rows
        ]

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        conn.close()


# ── 3. View full detail of a single project before scoring ────────────────────
@router.get('/project-detail/{project_id}')
def project_detail(project_id: int, user = Depends(verify_token)):
    """
    Full project info + team members + how many judges have scored it so far.
    """
    conn   = get_connection()
    cursor = conn.cursor()

    try:
        judge_id = get_judge_id(user["user_id"], cursor)

        # Confirm this judge is assigned to the event this project belongs to
        cursor.execute(
            '''
            SELECT 1
            FROM   EventJudges ej
            INNER JOIN Teams    t  ON ej.event_id = t.event_id
            INNER JOIN Projects p  ON t.team_id   = p.team_id
            WHERE  p.project_id = ? AND ej.judge_id = ?
            ''',
            (project_id, judge_id)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=403, detail='You are not assigned to this project')

        # Project + team + event info
        cursor.execute(
            '''
            SELECT
                p.project_id, p.project_name, p.github_link,
                p.description, p.status, p.submission_date,
                t.team_id, t.team_name,
                he.event_id, he.event_name
            FROM Projects p
            INNER JOIN Teams           t  ON p.team_id  = t.team_id
            INNER JOIN HackathonEvents he ON t.event_id = he.event_id
            WHERE p.project_id = ?
            ''',
            (project_id,)
        )
        r = cursor.fetchone()

        if not r:
            raise HTTPException(status_code=404, detail='Project not found')

        # All team members
        cursor.execute(
            '''
            SELECT u.firstname, u.lastname, u.email, tm.participant_id
            FROM   TeamMembers  tm
            INNER JOIN Participants p2 ON tm.participant_id = p2.participant_id
            INNER JOIN Users        u  ON p2.user_id        = u.user_id
            WHERE  tm.team_id = ?
            ''',
            (r.team_id,)
        )
        members = cursor.fetchall()

        # Aggregate evaluation stats so far (from all judges)
        cursor.execute(
            '''
            SELECT COUNT(*) AS eval_count, AVG(score) AS avg_score
            FROM   Evaluations
            WHERE  project_id = ?
            ''',
            (project_id,)
        )
        stats = cursor.fetchone()

        return {
            'project_id'        : r.project_id,
            'project_name'      : r.project_name,
            'github_link'       : r.github_link,
            'description'       : r.description,
            'status'            : r.status,
            'submission_date'   : str(r.submission_date),
            'team_id'           : r.team_id,
            'team_name'         : r.team_name,
            'event_id'          : r.event_id,
            'event_name'        : r.event_name,
            'evaluations_done'  : stats.eval_count if stats else 0,
            'current_avg_score' : round(float(stats.avg_score), 2) if stats.avg_score else None,
            'team_members'      : [
                {
                    'participant_id': m.participant_id,
                    'name'          : m.firstname + ' ' + m.lastname,
                    'email'         : m.email,
                }
                for m in members
            ],
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        conn.close()


# ── 4. Submit evaluation ───────────────────────────────────────────────────────
@router.post('/evaluate')
async def evaluate_project(
    data: EvaluateRequest,
    user = Depends(verify_token)
):
    """
    Required: project_id, score (0-100)
    Optional: feedback
    """
    conn   = get_connection()
    cursor = conn.cursor()

    try:
        judge_id = get_judge_id(user["user_id"], cursor)

        if data.score < 0 or data.score > 100:
            raise HTTPException(status_code=400, detail='Score must be between 0 and 100')

        cursor.execute(
            '''
            SELECT ej.judge_id
            FROM   EventJudges ej
            INNER JOIN Teams    t  ON ej.event_id = t.event_id
            INNER JOIN Projects p  ON t.team_id   = p.team_id
            WHERE  p.project_id = ? AND ej.judge_id = ?
            ''',
            (data.project_id, judge_id)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=403, detail='You are not assigned to evaluate this project')

        # ── Block evaluation if event is completed ────────────────────────────
        cursor.execute(
            '''
            SELECT he.event_status
            FROM   HackathonEvents he
            INNER JOIN Teams    t  ON t.event_id  = he.event_id
            INNER JOIN Projects p  ON p.team_id   = t.team_id
            WHERE  p.project_id = ?
            ''',
            (data.project_id,)
        )
        event_row = cursor.fetchone()
        if event_row and event_row.event_status == 'completed':
            raise HTTPException(
                status_code=400,
                detail='Evaluations cannot be submitted after the event has been completed'
            )

        cursor.execute(
            'SELECT 1 FROM Evaluations WHERE project_id = ? AND judge_id = ?',
            (data.project_id, judge_id)
        )
        if cursor.fetchone():
            raise HTTPException(status_code=409, detail='You have already evaluated this project')

        cursor.execute(
            '''
            INSERT INTO Evaluations (project_id, judge_id, score, feedback)
            VALUES (?, ?, ?, ?)
            ''',
            (data.project_id, judge_id, data.score, data.feedback)
        )

        cursor.execute(
            '''
            SELECT COUNT(*)
            FROM   EventJudges ej
            INNER JOIN Teams    t  ON ej.event_id = t.event_id
            INNER JOIN Projects p  ON t.team_id   = p.team_id
            WHERE  p.project_id = ?
            ''',
            (data.project_id,)
        )
        total_judges = cursor.fetchone()[0]

        if total_judges == 0:
            raise HTTPException(status_code=500, detail='No judges assigned to this event')

        cursor.execute(
            'SELECT COUNT(*) FROM Evaluations WHERE project_id = ?',
            (data.project_id,)
        )
        done = cursor.fetchone()[0]

        if done >= total_judges:
            cursor.execute(
                "UPDATE Projects SET status = 'evaluated' WHERE project_id = ?",
                (data.project_id,)
            )

        conn.commit()

        return {
            'success'        : True,
            'message'        : 'Evaluation submitted successfully',
            'judges_done'    : done,
            'judges_total'   : total_judges,
            'fully_evaluated': done >= total_judges,
        }

    except HTTPException:
        conn.rollback()
        raise

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        conn.close()


# ── 5. Update feedback on an existing evaluation ──────────────────────────────
@router.put('/update-feedback')
async def update_feedback(
    data: UpdateFeedbackRequest,
    user = Depends(verify_token)
):
    """
    Required: project_id, feedback
    Score cannot be changed to keep results fair.
    """
    conn   = get_connection()
    cursor = conn.cursor()

    try:
        judge_id = get_judge_id(user["user_id"], cursor)

        cursor.execute(
            'SELECT 1 FROM Evaluations WHERE project_id = ? AND judge_id = ?',
            (data.project_id, judge_id)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail='No evaluation found. Submit an evaluation first.')

        cursor.execute(
            '''
            UPDATE Evaluations
            SET    feedback = ?
            WHERE  project_id = ? AND judge_id = ?
            ''',
            (data.feedback, data.project_id, judge_id)
        )
        conn.commit()

        return {'success': True, 'message': 'Feedback updated successfully'}

    except HTTPException:
        raise

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        conn.close()


# ── 6. View my past evaluations ───────────────────────────────────────────────
@router.get('/my-evaluations')
def my_evaluations(user = Depends(verify_token)):
    """
    Full history of all evaluations this judge has submitted.
    """
    conn   = get_connection()
    cursor = conn.cursor()

    try:
        judge_id = get_judge_id(user["user_id"], cursor)

        cursor.execute(
            '''
            SELECT
                ev.evaluation_id,
                p.project_id,
                p.project_name,
                t.team_name,
                he.event_name,
                ev.score,
                ev.feedback
            FROM   Evaluations     ev
            INNER JOIN Projects        p  ON ev.project_id = p.project_id
            INNER JOIN Teams           t  ON p.team_id     = t.team_id
            INNER JOIN HackathonEvents he ON t.event_id    = he.event_id
            WHERE  ev.judge_id = ?
            ORDER  BY ev.evaluation_id DESC
            ''',
            (judge_id,)
        )
        rows = cursor.fetchall()

        return [
            {
                'evaluation_id': r.evaluation_id,
                'project_id'   : r.project_id,
                'project_name' : r.project_name,
                'team_name'    : r.team_name,
                'event_name'   : r.event_name,
                'score'        : float(r.score),
                'feedback'     : r.feedback,
            }
            for r in rows
        ]

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        conn.close()


# ── 7. View leaderboard for a specific event ──────────────────────────────────
@router.get('/event-leaderboard/{event_id}')
def event_leaderboard(event_id: int, user = Depends(verify_token)):
    """
    Ranked list of teams for an event, by average score.
    Returns 404 if event does not exist.
    Returns 403 if judge is not assigned to this event.
    Only teams that have received at least one evaluation appear here.
    """
    conn   = get_connection()
    cursor = conn.cursor()

    try:
        judge_id = get_judge_id(user["user_id"], cursor)

        # ── Check event exists first → 404 if not ────────────────────────────
        cursor.execute(
            'SELECT 1 FROM HackathonEvents WHERE event_id = ?',
            (event_id,)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail='Event not found')

        # ── Then check judge is assigned → 403 if not ────────────────────────
        cursor.execute(
            'SELECT 1 FROM EventJudges WHERE event_id = ? AND judge_id = ?',
            (event_id, judge_id)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=403, detail='You are not assigned to this event')

        cursor.execute(
            '''
            SELECT
                t.team_id,
                t.team_name,
                p.project_id,
                p.project_name,
                COUNT(ev.evaluation_id) AS total_evaluations,
                AVG(ev.score)           AS average_score,
                MAX(ev.score)           AS highest_score,
                MIN(ev.score)           AS lowest_score
            FROM   Teams           t
            INNER JOIN Projects    p  ON p.team_id     = t.team_id
            INNER JOIN Evaluations ev ON ev.project_id = p.project_id
            WHERE  t.event_id = ?
            GROUP  BY t.team_id, t.team_name, p.project_id, p.project_name
            HAVING COUNT(ev.evaluation_id) = (
                SELECT COUNT(*) FROM EventJudges WHERE event_id = ?
            )
            ORDER  BY average_score DESC
            ''',
            (event_id, event_id)
        )
        rows = cursor.fetchall()

        if not rows:
            return {
                'message'    : 'Leaderboard is not available yet. All judges must evaluate all projects first.',
                'leaderboard': []
            }

        return [
            {
                'rank'             : rank,
                'team_id'          : r.team_id,
                'team_name'        : r.team_name,
                'project_id'       : r.project_id,
                'project_name'     : r.project_name,
                'total_evaluations': r.total_evaluations,
                'average_score'    : round(float(r.average_score), 2),
                'highest_score'    : float(r.highest_score) if r.highest_score is not None else None,
                'lowest_score'     : float(r.lowest_score)  if r.lowest_score  is not None else None,
            }
            for rank, r in enumerate(rows, start=1)
        ]

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        conn.close()


# ── 8. View judge profile ─────────────────────────────────────────────────────
@router.get('/profile')
def judge_profile(user = Depends(verify_token)):
    """
    Full profile: personal info + all degrees + all phone numbers.
    """
    conn   = get_connection()
    cursor = conn.cursor()

    try:
        judge_id = get_judge_id(user["user_id"], cursor)

        cursor.execute(
            '''
            SELECT u.firstname, u.lastname, u.email, u.cnic, u.created_at,
                   j.commission_per_eval
            FROM   Judges j
            INNER JOIN Users u ON j.user_id = u.user_id
            WHERE  j.judge_id = ?
            ''',
            (judge_id,)
        )
        r = cursor.fetchone()

        if not r:
            raise HTTPException(status_code=404, detail='Judge not found')

        cursor.execute(
            'SELECT degree FROM Degrees WHERE judge_id = ?',
            (judge_id,)
        )
        degrees = [row.degree for row in cursor.fetchall()]

        cursor.execute(
            '''
            SELECT tel.phone_number
            FROM   Telephones tel
            INNER JOIN Judges j ON tel.user_id = j.user_id
            WHERE  j.judge_id = ?
            ''',
            (judge_id,)
        )
        phones = [row.phone_number for row in cursor.fetchall()]

        return {
            'name'               : r.firstname + ' ' + r.lastname,
            'email'              : r.email,
            'cnic'               : r.cnic,
            'created_at'         : str(r.created_at),
            'commission_per_eval': float(r.commission_per_eval),
            'degrees'            : degrees,
            'phone_numbers'      : phones,
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        conn.close()


# ── 9. View events assigned to this judge ─────────────────────────────────────
@router.get('/my-events')
def my_events(user = Depends(verify_token)):
    """
    All events + how many projects are pending evaluation by this judge.
    """
    conn   = get_connection()
    cursor = conn.cursor()

    try:
        judge_id = get_judge_id(user["user_id"], cursor)

        cursor.execute(
            '''
            SELECT
                he.event_id,
                he.event_name,
                he.start_date,
                he.end_date,
                he.event_status,
                ej.assigned_date,
                COUNT(DISTINCT p.project_id)  AS total_projects,
                COUNT(DISTINCT ev.project_id) AS evaluated_by_me
            FROM   EventJudges     ej
            INNER JOIN HackathonEvents he ON ej.event_id   = he.event_id
            LEFT  JOIN Teams           t  ON t.event_id    = he.event_id
            LEFT  JOIN Projects        p  ON p.team_id     = t.team_id
            LEFT  JOIN Evaluations     ev ON ev.project_id = p.project_id
                                         AND ev.judge_id   = ej.judge_id
            WHERE  ej.judge_id = ?
            GROUP  BY he.event_id, he.event_name, he.start_date,
                      he.end_date, he.event_status, ej.assigned_date
            ORDER  BY he.start_date DESC
            ''',
            (judge_id,)
        )
        rows = cursor.fetchall()

        return [
            {
                'event_id'       : r.event_id,
                'event_name'     : r.event_name,
                'start_date'     : str(r.start_date),
                'end_date'       : str(r.end_date),
                'event_status'   : r.event_status,
                'assigned_date'  : str(r.assigned_date),
                'total_projects' : r.total_projects,
                'evaluated_by_me': r.evaluated_by_me,
                'pending'        : r.total_projects - r.evaluated_by_me,
            }
            for r in rows
        ]

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        conn.close()