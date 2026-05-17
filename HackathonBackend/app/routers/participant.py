from fastapi import APIRouter, Request, Depends, HTTPException
from app.database import get_connection
from app.routers.auth import verify_token
from pydantic import BaseModel
from typing import Optional
import random
import string
from datetime import date

router = APIRouter(prefix='/participant', tags=['Participant'])


# ── REQUEST MODELS ────────────────────────────────────────────────
class RegisterEventRequest(BaseModel):
    event_id: int

class CreateTeamRequest(BaseModel):
    event_id : int
    team_name: str

class JoinTeamRequest(BaseModel):
    event_id  : int
    team_code : str

class LeaveTeamRequest(BaseModel):
    team_id: int

class SubmitProjectRequest(BaseModel):
    team_id     : int
    project_name: str
    github_link : Optional[str] = None
    description : Optional[str] = None


class UpdateProfileRequest(BaseModel):
    firstname   : Optional[str] = None
    middlename  : Optional[str] = None
    lastname    : Optional[str] = None
    email       : Optional[str] = None
    password    : Optional[str] = None
    date_of_birth: Optional[str] = None
    city        : Optional[str] = None
    institution : Optional[str] = None


# ── View all available events ─────────────────────────────────────────────────
@router.get('/events')
def view_events():

    conn   = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute(
            '''
            SELECT event_id, event_name, start_date, end_date,
                   last_date_of_registration, event_status
            FROM HackathonEvents
            ORDER BY start_date DESC
            '''
        )

        rows = cursor.fetchall()

        return [
            {
                'event_id'                  : r.event_id,
                'event_name'                : r.event_name,
                'start_date'                : str(r.start_date),
                'end_date'                  : str(r.end_date),
                'last_date_of_registration' : str(r.last_date_of_registration),
                'event_status'              : r.event_status,
            }
            for r in rows
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        conn.close()


# ── Register for an event ─────────────────────────────────────────────────────
@router.post('/register-event')
async def register_event(
    data: RegisterEventRequest,
    user = Depends(verify_token)
):

    if user["role"] != "participant":
        raise HTTPException(status_code=403, detail="Participants only")

    participant_id = user["participant_id"]

    conn   = get_connection()
    cursor = conn.cursor()

    try:

        # Check event exists
        cursor.execute(
            '''
            SELECT last_date_of_registration, event_status
            FROM HackathonEvents
            WHERE event_id = ?
            ''',
            (data.event_id,)
        )

        event = cursor.fetchone()

        if not event:
            raise HTTPException(status_code=404, detail='Event not found')

        if event.event_status != 'upcoming':
            raise HTTPException(status_code=400, detail='Registration is closed for this event')

        if date.today() > event.last_date_of_registration:
            raise HTTPException(status_code=400, detail='Registration deadline has passed')

        cursor.execute(
            '''
            SELECT 1
            FROM EventRegistrations
            WHERE event_id = ? AND participant_id = ?
            ''',
            (data.event_id, participant_id)
        )

        if cursor.fetchone():
            raise HTTPException(status_code=400, detail='You are already registered for this event')

        cursor.execute(
            '''
            INSERT INTO EventRegistrations (event_id, participant_id)
            VALUES (?, ?)
            ''',
            (data.event_id, participant_id)
        )

        conn.commit()

        return {'success': True, 'message': 'Registered in event successfully'}

    except HTTPException:
        raise

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        conn.close()


# ── View my registered events ─────────────────────────────────────────────────
@router.get('/my-events/{participant_id}')
def my_events(
    participant_id: int,
    user = Depends(verify_token)
):

    if user["role"] != "participant":
        raise HTTPException(status_code=403, detail="Participants only")

    if participant_id != user["participant_id"]:
        raise HTTPException(status_code=403, detail="Unauthorized access")

    conn   = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute(
            '''
            SELECT he.event_id, he.event_name, he.start_date,
                   he.end_date, he.event_status, er.registration_date
            FROM EventRegistrations er
            INNER JOIN HackathonEvents he
                ON er.event_id = he.event_id
            WHERE er.participant_id = ?
            ORDER BY he.start_date DESC
            ''',
            (participant_id,)
        )

        rows = cursor.fetchall()

        return [
            {
                'event_id'          : r.event_id,
                'event_name'        : r.event_name,
                'start_date'        : str(r.start_date),
                'end_date'          : str(r.end_date),
                'event_status'      : r.event_status,
                'registration_date' : str(r.registration_date),
            }
            for r in rows
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        conn.close()


# ── Create a team ─────────────────────────────────────────────────────────────
@router.post('/create-team')
async def create_team(
    data: CreateTeamRequest,
    user = Depends(verify_token)
):

    if user["role"] != "participant":
        raise HTTPException(status_code=403, detail="Participants only")

    team_name = data.team_name.strip()
    if not team_name:
        raise HTTPException(status_code=400, detail='team_name is required')

    team_lead = user["participant_id"]

    conn   = get_connection()
    cursor = conn.cursor()

    try:

        # Check event exists
        cursor.execute(
            '''
            SELECT event_status
            FROM HackathonEvents
            WHERE event_id = ?
            ''',
            (data.event_id,)
        )

        event = cursor.fetchone()

        if not event:
            raise HTTPException(status_code=404, detail='Event not found')

        if event.event_status != 'upcoming':
            raise HTTPException(status_code=400, detail='Teams can only be created for upcoming events')

        cursor.execute(
            '''
            SELECT 1
            FROM EventRegistrations
            WHERE event_id = ? AND participant_id = ?
            ''',
            (data.event_id, team_lead)
        )

        if not cursor.fetchone():
            raise HTTPException(status_code=403, detail='You must register in the event before creating a team')

        cursor.execute(
            '''
            SELECT 1
            FROM TeamMembers
            WHERE event_id = ? AND participant_id = ?
            ''',
            (data.event_id, team_lead)
        )

        if cursor.fetchone():
            raise HTTPException(status_code=400, detail='You are already in a team for this event')

        cursor.execute(
            '''
            SELECT 1
            FROM Teams
            WHERE event_id = ? AND team_name = ?
            ''',
            (data.event_id, team_name)
        )

        if cursor.fetchone():
            raise HTTPException(status_code=400, detail='Team name already exists in this event')

        # Generate unique team code (max 20 attempts to avoid infinite loop)
        team_code = None

        for _ in range(20):

            candidate = ''.join(
                random.choices(string.ascii_uppercase + string.digits, k=6)
            )

            cursor.execute(
                'SELECT 1 FROM Teams WHERE team_code = ?',
                (candidate,)
            )

            if not cursor.fetchone():
                team_code = candidate
                break

        if not team_code:
            raise HTTPException(
                status_code=500,
                detail='Could not generate a unique team code. Please try again.'
            )

        # Create team
        cursor.execute(
            '''
            INSERT INTO Teams
            (event_id, team_name, team_lead, team_code, created_at)
            OUTPUT INSERTED.team_id
            VALUES (?, ?, ?, ?, GETDATE())
            ''',
            (data.event_id, team_name, team_lead, team_code)
        )

        team_id = cursor.fetchone()[0]

        cursor.execute(
            '''
            INSERT INTO TeamMembers
            (team_id, event_id, participant_id)
            VALUES (?, ?, ?)
            ''',
            (team_id, data.event_id, team_lead)
        )

        conn.commit()

        return {
            'success'  : True,
            'message'  : 'Team created successfully',
            'team_id'  : team_id,
            'team_code': team_code
        }

    except HTTPException:
        raise

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        conn.close()


# ── Join a team via code ──────────────────────────────────────────────────────
@router.post('/join-team')
async def join_team(
    data: JoinTeamRequest,
    user = Depends(verify_token)
):

    if user["role"] != "participant":
        raise HTTPException(status_code=403, detail="Participants only")

    participant_id = user["participant_id"]

    conn   = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute(
            '''
            SELECT event_status, max_team_size
            FROM HackathonEvents
            WHERE event_id = ?
            ''',
            (data.event_id,)
        )

        event = cursor.fetchone()

        if not event:
            raise HTTPException(status_code=404, detail='Event not found')

        if event.event_status != 'upcoming':
            raise HTTPException(status_code=400, detail='Cannot join teams for this event now')

        cursor.execute(
            '''
            SELECT 1
            FROM EventRegistrations
            WHERE event_id = ? AND participant_id = ?
            ''',
            (data.event_id, participant_id)
        )

        if not cursor.fetchone():
            raise HTTPException(status_code=403, detail='You must register in the event before joining a team')

        cursor.execute(
            '''
            SELECT 1
            FROM TeamMembers
            WHERE event_id = ? AND participant_id = ?
            ''',
            (data.event_id, participant_id)
        )

        if cursor.fetchone():
            raise HTTPException(status_code=400, detail='You are already in a team for this event')

        cursor.execute(
            '''
            SELECT team_id
            FROM Teams
            WHERE team_code = ? AND event_id = ?
            ''',
            (data.team_code, data.event_id)
        )

        team = cursor.fetchone()

        if not team:
            raise HTTPException(status_code=404, detail='Invalid team code or wrong event')

        team_id = team.team_id

        cursor.execute(
            '''
            SELECT COUNT(*) AS member_count
            FROM TeamMembers
            WHERE team_id = ?
            ''',
            (team_id,)
        )

        current_members = cursor.fetchone().member_count

        if current_members >= event.max_team_size:
            raise HTTPException(status_code=400, detail='Team is full')

        cursor.execute(
            '''
            INSERT INTO TeamMembers
            (team_id, event_id, participant_id)
            VALUES (?, ?, ?)
            ''',
            (team_id, data.event_id, participant_id)
        )

        conn.commit()

        return {'success': True, 'message': 'Joined team successfully'}

    except HTTPException:
        raise

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        conn.close()


# ── View my team for an event ─────────────────────────────────────────────────
@router.get('/my-team/{participant_id}/{event_id}')
def my_team(
    participant_id: int,
    event_id: int,
    user = Depends(verify_token)
):

    if user["role"] != "participant":
        raise HTTPException(status_code=403, detail="Participants only")

    if participant_id != user["participant_id"]:
        raise HTTPException(status_code=403, detail="Unauthorized access")

    conn   = get_connection()
    cursor = conn.cursor()

    try:

        # Get team info
        cursor.execute(
            '''
            SELECT t.team_id, t.team_name, t.team_code
            FROM Teams t
            INNER JOIN TeamMembers tm
                ON t.team_id = tm.team_id
            WHERE tm.participant_id = ? AND tm.event_id = ?
            ''',
            (participant_id, event_id)
        )

        team = cursor.fetchone()

        if not team:
            raise HTTPException(status_code=404, detail='You are not in any team for this event')

        # Get team members
        cursor.execute(
            '''
            SELECT u.firstname, u.lastname, u.email,
                   tm.participant_id
            FROM TeamMembers tm
            INNER JOIN Participants p
                ON tm.participant_id = p.participant_id
            INNER JOIN Users u
                ON p.user_id = u.user_id
            WHERE tm.team_id = ?
            ''',
            (team.team_id,)
        )

        members = cursor.fetchall()

        return {
            'team_id'  : team.team_id,
            'team_name': team.team_name,
            'team_code': team.team_code,
            'members'  : [
                {
                    'participant_id': m.participant_id,
                    'name'          : m.firstname + ' ' + m.lastname,
                    'email'         : m.email,
                }
                for m in members
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        conn.close()


# ── Leave a team ──────────────────────────────────────────────────────────────
@router.delete('/leave-team')
async def leave_team(
    data: LeaveTeamRequest,
    user = Depends(verify_token)
):

    if user["role"] != "participant":
        raise HTTPException(status_code=403, detail="Participants only")

    participant_id = user["participant_id"]

    conn   = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute(
            '''
            SELECT t.team_lead, he.event_status
            FROM Teams t
            INNER JOIN HackathonEvents he
                ON t.event_id = he.event_id
            WHERE t.team_id = ?
            ''',
            (data.team_id,)
        )

        team = cursor.fetchone()

        if not team:
            raise HTTPException(status_code=404, detail='Team not found')

        if team.event_status != 'upcoming':
            raise HTTPException(status_code=400, detail='You cannot leave a team after the event has started')

        if team.team_lead == participant_id:
            raise HTTPException(status_code=400, detail='Team lead cannot leave. Delete the team instead.')

        cursor.execute(
            '''
            SELECT 1
            FROM TeamMembers
            WHERE team_id = ? AND participant_id = ?
            ''',
            (data.team_id, participant_id)
        )

        if not cursor.fetchone():
            raise HTTPException(status_code=403, detail='Participant is not a member of this team')

        cursor.execute(
            '''
            DELETE FROM TeamMembers
            WHERE team_id = ? AND participant_id = ?
            ''',
            (data.team_id, participant_id)
        )

        conn.commit()

        return {'success': True, 'message': 'Left team successfully'}

    except HTTPException:
        raise

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        conn.close()


# ── Submit a project ──────────────────────────────────────────────────────────
@router.post('/submit-project')
async def submit_project(
    data: SubmitProjectRequest,
    user = Depends(verify_token)
):

    if user["role"] != "participant":
        raise HTTPException(status_code=403, detail="Participants only")

    participant_id = user["participant_id"]

    conn   = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute(
            '''
            SELECT t.team_id, he.event_status
            FROM Teams t
            INNER JOIN HackathonEvents he
                ON t.event_id = he.event_id
            WHERE t.team_id = ?
            ''',
            (data.team_id,)
        )

        team = cursor.fetchone()

        if not team:
            raise HTTPException(status_code=404, detail='Team not found')

        if team.event_status != 'ongoing':
            raise HTTPException(status_code=400, detail='Projects can only be submitted during ongoing events')

        cursor.execute(
            '''
            SELECT 1
            FROM TeamMembers
            WHERE team_id = ? AND participant_id = ?
            ''',
            (data.team_id, participant_id)
        )

        if not cursor.fetchone():
            raise HTTPException(status_code=403, detail="You are not a member of this team")

        cursor.execute(
            'SELECT 1 FROM Projects WHERE team_id = ?',
            (data.team_id,)
        )

        if cursor.fetchone():
            raise HTTPException(status_code=400, detail='Your team has already submitted a project')

        cursor.execute(
            '''
            INSERT INTO Projects
            (team_id, project_name, github_link, description, status)
            OUTPUT INSERTED.project_id
            VALUES (?, ?, ?, ?, 'submitted')
            ''',
            (
                data.team_id,
                data.project_name.strip(),
                data.github_link,
                data.description
            )
        )

        project_id = cursor.fetchone()[0]
        conn.commit()

        return {
            'success'   : True,
            'message'   : 'Project submitted successfully',
            'project_id': project_id
        }

    except HTTPException:
        raise

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        conn.close()


# ── View my team's project ────────────────────────────────────────────────────
@router.get('/my-project/{team_id}')
def my_project(
    team_id: int,
    user = Depends(verify_token)
):

    if user["role"] != "participant":
        raise HTTPException(status_code=403, detail="Participants only")

    participant_id = user["participant_id"]

    conn   = get_connection()
    cursor = conn.cursor()

    try:

        # Verify caller belongs to this team
        cursor.execute(
            '''
            SELECT 1
            FROM TeamMembers
            WHERE team_id = ? AND participant_id = ?
            ''',
            (team_id, participant_id)
        )

        if not cursor.fetchone():
            raise HTTPException(status_code=403, detail="Unauthorized access")

        cursor.execute(
            '''
            SELECT project_id, project_name, github_link,
                   description, status, submission_date
            FROM Projects
            WHERE team_id = ?
            ''',
            (team_id,)
        )

        r = cursor.fetchone()

        if not r:
            raise HTTPException(status_code=404, detail='No project submitted yet')

        return {
            'project_id'     : r.project_id,
            'project_name'   : r.project_name,
            'github_link'    : r.github_link,
            'description'    : r.description,
            'status'         : r.status,
            'submission_date': str(r.submission_date),
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        conn.close()


# ── View my profile ───────────────────────────────────────────────────────────
@router.get('/profile/{participant_id}')
def profile(
    participant_id: int,
    user = Depends(verify_token)
):

    if user["role"] != "participant":
        raise HTTPException(status_code=403, detail="Participants only")

    if participant_id != user["participant_id"]:
        raise HTTPException(status_code=403, detail="Unauthorized access")

    conn   = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute(
            '''
            SELECT u.firstname, u.middlename, u.lastname,
                   u.email, u.cnic, u.created_at,
                   p.date_of_birth, p.city, p.institution
            FROM Participants p
            INNER JOIN Users u
                ON p.user_id = u.user_id
            WHERE p.participant_id = ?
            ''',
            (participant_id,)
        )

        r = cursor.fetchone()

        if not r:
            raise HTTPException(status_code=404, detail='Participant not found')

        # Get phone numbers
        cursor.execute(
            '''
            SELECT t.phone_number
            FROM Telephones t
            INNER JOIN Participants p
                ON t.user_id = p.user_id
            WHERE p.participant_id = ?
            ''',
            (participant_id,)
        )

        phones = [row.phone_number for row in cursor.fetchall()]

        return {
            'name'         : ' '.join(filter(None, [r.firstname, r.middlename, r.lastname])),
            'email'        : r.email,
            'cnic'         : r.cnic,
            'date_of_birth': str(r.date_of_birth) if r.date_of_birth else None,
            'city'         : r.city,
            'institution'  : r.institution,
            'created_at'   : str(r.created_at),
            'phone_numbers': phones,
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        conn.close()


# ── Update my profile ─────────────────────────────────────────────────────────
@router.put('/update-profile/{participant_id}')
async def update_profile(
    participant_id: int,
    data: UpdateProfileRequest,
    user = Depends(verify_token)
):
    """
    Participant updates their own profile.
    Cannot change: participant_id, user_id, cnic, role.

    Updatable (Users table):
        firstname, middlename, lastname, email, password

    Updatable (Participants table):
        date_of_birth, city, institution
    """

    if user["role"] != "participant":
        raise HTTPException(status_code=403, detail="Participants only")

    if participant_id != user["participant_id"]:
        raise HTTPException(status_code=403, detail="Unauthorized access")

    conn   = get_connection()
    cursor = conn.cursor()

    try:

        # Get user_id for this participant
        cursor.execute(
            'SELECT user_id FROM Participants WHERE participant_id = ?',
            (participant_id,)
        )
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Participant not found")

        p_user_id = row.user_id

        # ── Validate email uniqueness if being changed ────────────
        if data.email is not None:
            if not data.email.strip():
                raise HTTPException(status_code=400, detail="email cannot be empty")
            cursor.execute(
                'SELECT 1 FROM Users WHERE email = ? AND user_id != ?',
                (data.email.strip(), p_user_id)
            )
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="Email already in use by another account")

        # ── Validate date_of_birth format if provided ─────────────
        if data.date_of_birth is not None:
            try:
                date.fromisoformat(data.date_of_birth)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid date_of_birth format. Use YYYY-MM-DD."
                )

        # ── Update Users table ────────────────────────────────────
        user_fields = {}
        if data.firstname  is not None:
            if not data.firstname.strip():
                raise HTTPException(status_code=400, detail="firstname cannot be empty")
            user_fields['firstname'] = data.firstname.strip()
        if data.middlename is not None: user_fields['middlename'] = data.middlename.strip() or None
        if data.lastname   is not None:
            if not data.lastname.strip():
                raise HTTPException(status_code=400, detail="lastname cannot be empty")
            user_fields['lastname'] = data.lastname.strip()
        if data.email      is not None: user_fields['email']    = data.email.strip()
        if data.password   is not None:
            if not data.password:
                raise HTTPException(status_code=400, detail="password cannot be empty")
            user_fields['password'] = data.password

        if user_fields:
            set_clause = ', '.join(f"{k} = ?" for k in user_fields)
            cursor.execute(
                f'UPDATE Users SET {set_clause} WHERE user_id = ?',
                (*user_fields.values(), p_user_id)
            )

        # ── Update Participants table ─────────────────────────────
        participant_fields = {}
        if data.date_of_birth is not None: participant_fields['date_of_birth'] = data.date_of_birth
        if data.city          is not None: participant_fields['city']          = data.city.strip() or None
        if data.institution   is not None: participant_fields['institution']   = data.institution.strip() or None

        if participant_fields:
            set_clause = ', '.join(f"{k} = ?" for k in participant_fields)
            cursor.execute(
                f'UPDATE Participants SET {set_clause} WHERE participant_id = ?',
                (*participant_fields.values(), participant_id)
            )

        if not user_fields and not participant_fields:
            raise HTTPException(status_code=400, detail="No fields provided to update")

        conn.commit()

        return {'success': True, 'message': 'Profile updated successfully'}

    except HTTPException:
        raise

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        conn.close()


# ── View results for all enrolled events (only fully evaluated ones) ──────────
@router.get('/my-results/{participant_id}')
def my_results(
    participant_id: int,
    user = Depends(verify_token)
):
    """
    Returns leaderboard results for every event the participant is registered in.
    Each event entry includes a results_ready flag:
      - True  → all judges have evaluated all projects; leaderboard is included
      - False → evaluation still in progress; leaderboard is empty
    """

    if user["role"] != "participant":
        raise HTTPException(status_code=403, detail="Participants only")

    if participant_id != user["participant_id"]:
        raise HTTPException(status_code=403, detail="Unauthorized access")

    conn   = get_connection()
    cursor = conn.cursor()

    try:

        # ── Fetch all events this participant is registered in ────
        cursor.execute(
            '''
            SELECT he.event_id, he.event_name, he.event_status
            FROM EventRegistrations er
            INNER JOIN HackathonEvents he ON er.event_id = he.event_id
            WHERE er.participant_id = ?
            ORDER BY he.start_date DESC
            ''',
            (participant_id,)
        )
        events = cursor.fetchall()

        if not events:
            return []

        results = []

        for ev in events:

            event_id     = ev.event_id
            event_name   = ev.event_name
            event_status = ev.event_status

            # ── Count judges assigned to this event ───────────────
            cursor.execute(
                'SELECT COUNT(*) FROM EventJudges WHERE event_id = ?',
                (event_id,)
            )
            total_judges = cursor.fetchone()[0]

            # ── Count submitted projects in this event ────────────
            cursor.execute(
                '''
                SELECT COUNT(*) FROM Projects p
                INNER JOIN Teams t ON p.team_id = t.team_id
                WHERE t.event_id = ?
                ''',
                (event_id,)
            )
            total_projects = cursor.fetchone()[0]

            # ── Determine if all projects are fully evaluated ─────
            fully_evaluated = False

            if total_judges > 0 and total_projects > 0:
                cursor.execute(
                    '''
                    SELECT COUNT(*) FROM Projects p
                    INNER JOIN Teams t ON p.team_id = t.team_id
                    WHERE t.event_id = ?
                      AND (
                          SELECT COUNT(*) FROM Evaluations e
                          WHERE e.project_id = p.project_id
                      ) < ?
                    ''',
                    (event_id, total_judges)
                )
                incomplete = cursor.fetchone()[0]
                fully_evaluated = (incomplete == 0)

            if not fully_evaluated:
                results.append({
                    'event_id'     : event_id,
                    'event_name'   : event_name,
                    'event_status' : event_status,
                    'results_ready': False,
                    'message'      : 'Results not available yet. Evaluation is still in progress.',
                    'leaderboard'  : []
                })
                continue

            # ── Fetch ranked leaderboard for this event ───────────
            cursor.execute(
                '''
                SELECT
                    t.team_id,
                    t.team_name,
                    p.project_id,
                    p.project_name,
                    p.github_link,
                    COUNT(ev.evaluation_id) AS total_evaluations,
                    AVG(ev.score)           AS average_score,
                    MAX(ev.score)           AS highest_score,
                    MIN(ev.score)           AS lowest_score
                FROM   Teams           t
                INNER JOIN Projects    p  ON p.team_id     = t.team_id
                INNER JOIN Evaluations ev ON ev.project_id = p.project_id
                WHERE  t.event_id = ?
                GROUP  BY t.team_id, t.team_name, p.project_id, p.project_name, p.github_link
                ORDER  BY average_score DESC
                ''',
                (event_id,)
            )
            rows = cursor.fetchall()

            results.append({
                'event_id'     : event_id,
                'event_name'   : event_name,
                'event_status' : event_status,
                'results_ready': True,
                'leaderboard'  : [
                    {
                        'rank'             : rank,
                        'team_id'          : r.team_id,
                        'team_name'        : r.team_name,
                        'project_id'       : r.project_id,
                        'project_name'     : r.project_name,
                        'github_link'      : r.github_link,
                        'total_evaluations': r.total_evaluations,
                        'average_score'    : round(float(r.average_score), 2),
                        'highest_score'    : float(r.highest_score),
                        'lowest_score'     : float(r.lowest_score),
                    }
                    for rank, r in enumerate(rows, start=1)
                ]
            })

        return results

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        conn.close()
