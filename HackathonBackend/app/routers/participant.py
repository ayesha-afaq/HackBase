import random
import string
from datetime import date

from fastapi import APIRouter, Request, Depends, HTTPException
from app.database import get_connection
from app.routers.auth import verify_token

router = APIRouter(prefix='/participant', tags=['Participant'])


# ── View all available events ─────────────────────────────────────────────────
@router.get('/events')
def view_events():

    conn   = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute(
            '''
            SELECT event_id, event_name, start_date, end_date,
                   last_date_of_registration, max_team_size,
                   event_details, event_status,
                   first_prize, second_prize, third_prize
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
                'max_team_size'             : r.max_team_size,
                'event_details'             : r.event_details,
                'event_status'              : r.event_status,
                'first_prize'               : float(r.first_prize),
                'second_prize'              : float(r.second_prize),
                'third_prize'               : float(r.third_prize),
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
    request: Request,
    user = Depends(verify_token)
):

    if user["role"] != "participant":
        raise HTTPException(status_code=403, detail="Participants only")

    data = await request.json()

    if not data.get('event_id'):
        raise HTTPException(status_code=400, detail='event_id is required')

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
            (data['event_id'],)
        )

        event = cursor.fetchone()

        if not event:
            return {'message': 'Event not found'}

        # Only upcoming events allowed
        if event.event_status != 'upcoming':
            return {'message': 'Registration is closed for this event'}

        # Check registration deadline
        if date.today() > event.last_date_of_registration:
            return {'message': 'Registration deadline has passed'}

        # Already registered?
        cursor.execute(
            '''
            SELECT 1
            FROM EventRegistrations
            WHERE event_id = ? AND participant_id = ?
            ''',
            (data['event_id'], participant_id)
        )

        if cursor.fetchone():
            return {'message': 'You are already registered for this event'}

        # Register participant
        cursor.execute(
            '''
            INSERT INTO EventRegistrations (event_id, participant_id)
            VALUES (?, ?)
            ''',
            (data['event_id'], participant_id)
        )

        conn.commit()

        return {'message': 'Registered in event successfully'}

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
    request: Request,
    user = Depends(verify_token)
):

    if user["role"] != "participant":
        raise HTTPException(status_code=403, detail="Participants only")

    data = await request.json()

    if not data.get('event_id'):
        raise HTTPException(status_code=400, detail='event_id is required')

    team_name = (data.get('team_name') or '').strip()
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
            (data['event_id'],)
        )

        event = cursor.fetchone()

        if not event:
            return {'message': 'Event not found'}

        # Only upcoming events
        if event.event_status != 'upcoming':
            return {'message': 'Teams can only be created for upcoming events'}

        # Participant must be registered
        cursor.execute(
            '''
            SELECT 1
            FROM EventRegistrations
            WHERE event_id = ? AND participant_id = ?
            ''',
            (data['event_id'], team_lead)
        )

        if not cursor.fetchone():
            return {'message': 'You must register in the event before creating a team'}

        # Already in a team?
        cursor.execute(
            '''
            SELECT 1
            FROM TeamMembers
            WHERE event_id = ? AND participant_id = ?
            ''',
            (data['event_id'], team_lead)
        )

        if cursor.fetchone():
            return {'message': 'You are already in a team for this event'}

        # Team name already exists?
        cursor.execute(
            '''
            SELECT 1
            FROM Teams
            WHERE event_id = ? AND team_name = ?
            ''',
            (data['event_id'], team_name)
        )

        if cursor.fetchone():
            return {'message': 'Team name already exists in this event'}

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
            (data['event_id'], team_name, team_lead, team_code)
        )

        team_id = cursor.fetchone()[0]

        # Add team lead as first member
        cursor.execute(
            '''
            INSERT INTO TeamMembers
            (team_id, event_id, participant_id)
            VALUES (?, ?, ?)
            ''',
            (team_id, data['event_id'], team_lead)
        )

        conn.commit()

        return {
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
    request: Request,
    user = Depends(verify_token)
):

    if user["role"] != "participant":
        raise HTTPException(status_code=403, detail="Participants only")

    data = await request.json()

    if not data.get('event_id'):
        raise HTTPException(status_code=400, detail='event_id is required')
    if not data.get('team_code'):
        raise HTTPException(status_code=400, detail='team_code is required')

    participant_id = user["participant_id"]

    conn   = get_connection()
    cursor = conn.cursor()

    try:

        # Check event exists
        cursor.execute(
            '''
            SELECT event_status, max_team_size
            FROM HackathonEvents
            WHERE event_id = ?
            ''',
            (data['event_id'],)
        )

        event = cursor.fetchone()

        if not event:
            return {'message': 'Event not found'}

        # Only upcoming events
        if event.event_status != 'upcoming':
            return {'message': 'Cannot join teams for this event now'}

        # Participant must be registered
        cursor.execute(
            '''
            SELECT 1
            FROM EventRegistrations
            WHERE event_id = ? AND participant_id = ?
            ''',
            (data['event_id'], participant_id)
        )

        if not cursor.fetchone():
            return {'message': 'You must register in the event before joining a team'}

        # Already in a team?
        cursor.execute(
            '''
            SELECT 1
            FROM TeamMembers
            WHERE event_id = ? AND participant_id = ?
            ''',
            (data['event_id'], participant_id)
        )

        if cursor.fetchone():
            return {'message': 'You are already in a team for this event'}

        # Find team
        cursor.execute(
            '''
            SELECT team_id
            FROM Teams
            WHERE team_code = ? AND event_id = ?
            ''',
            (data['team_code'], data['event_id'])
        )

        team = cursor.fetchone()

        if not team:
            return {'message': 'Invalid team code or wrong event'}

        team_id = team.team_id

        # Count current members
        cursor.execute(
            '''
            SELECT COUNT(*) AS member_count
            FROM TeamMembers
            WHERE team_id = ?
            ''',
            (team_id,)
        )

        current_members = cursor.fetchone().member_count

        # Team full?
        if current_members >= event.max_team_size:
            return {'message': 'Team is full'}

        # Join team
        cursor.execute(
            '''
            INSERT INTO TeamMembers
            (team_id, event_id, participant_id)
            VALUES (?, ?, ?)
            ''',
            (team_id, data['event_id'], participant_id)
        )

        conn.commit()

        return {'message': 'Joined team successfully'}

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
            return {'message': 'You are not in any team for this event'}

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
    request: Request,
    user = Depends(verify_token)
):

    if user["role"] != "participant":
        raise HTTPException(status_code=403, detail="Participants only")

    data = await request.json()

    if not data.get('team_id'):
        raise HTTPException(status_code=400, detail='team_id is required')

    participant_id = user["participant_id"]

    conn   = get_connection()
    cursor = conn.cursor()

    try:

        # Check team exists and get event status in one query
        cursor.execute(
            '''
            SELECT t.team_lead, he.event_status
            FROM Teams t
            INNER JOIN HackathonEvents he
                ON t.event_id = he.event_id
            WHERE t.team_id = ?
            ''',
            (data['team_id'],)
        )

        team = cursor.fetchone()

        if not team:
            return {'message': 'Team not found'}

        # Cannot leave once event has started
        if team.event_status != 'upcoming':
            return {'message': 'You cannot leave a team after the event has started'}

        # Team lead cannot leave
        if team.team_lead == participant_id:
            return {'message': 'Team lead cannot leave. Delete the team instead.'}

        # Check membership
        cursor.execute(
            '''
            SELECT 1
            FROM TeamMembers
            WHERE team_id = ? AND participant_id = ?
            ''',
            (data['team_id'], participant_id)
        )

        if not cursor.fetchone():
            return {'message': 'Participant is not a member of this team'}

        # Remove member
        cursor.execute(
            '''
            DELETE FROM TeamMembers
            WHERE team_id = ? AND participant_id = ?
            ''',
            (data['team_id'], participant_id)
        )

        conn.commit()

        return {'message': 'Left team successfully'}

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
    request: Request,
    user = Depends(verify_token)
):

    if user["role"] != "participant":
        raise HTTPException(status_code=403, detail="Participants only")

    data = await request.json()

    if not data.get('team_id'):
        raise HTTPException(status_code=400, detail='team_id is required')
    if not (data.get('project_name') or '').strip():
        raise HTTPException(status_code=400, detail='project_name is required')

    participant_id = user["participant_id"]

    conn   = get_connection()
    cursor = conn.cursor()

    try:

        # Check team exists and get event status
        cursor.execute(
            '''
            SELECT t.team_id, he.event_status
            FROM Teams t
            INNER JOIN HackathonEvents he
                ON t.event_id = he.event_id
            WHERE t.team_id = ?
            ''',
            (data['team_id'],)
        )

        team = cursor.fetchone()

        if not team:
            return {'message': 'Team not found'}

        # Only ongoing events can submit
        if team.event_status != 'ongoing':
            return {'message': 'Projects can only be submitted during ongoing events'}

        # Confirm caller belongs to this team
        cursor.execute(
            '''
            SELECT 1
            FROM TeamMembers
            WHERE team_id = ? AND participant_id = ?
            ''',
            (data['team_id'], participant_id)
        )

        if not cursor.fetchone():
            raise HTTPException(
                status_code=403,
                detail="You are not a member of this team"
            )

        # Already submitted?
        cursor.execute(
            '''
            SELECT 1
            FROM Projects
            WHERE team_id = ?
            ''',
            (data['team_id'],)
        )

        if cursor.fetchone():
            return {'message': 'Your team has already submitted a project'}

        # Submit project
        cursor.execute(
            '''
            INSERT INTO Projects
            (team_id, project_name, github_link, description, status)
            OUTPUT INSERTED.project_id
            VALUES (?, ?, ?, ?, 'submitted')
            ''',
            (
                data['team_id'],
                data['project_name'].strip(),
                data.get('github_link'),
                data.get('description')
            )
        )

        project_id = cursor.fetchone()[0]

        conn.commit()

        return {
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
            return {'message': 'No project submitted yet'}

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
            return {'message': 'Participant not found'}

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
