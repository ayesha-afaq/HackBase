from fastapi import APIRouter, Request, Depends, HTTPException
from app.database import get_connection
from app.routers.auth import verify_token
from datetime import date

router = APIRouter(prefix='/organizer', tags=['Organizer'])


# ── HELPER FUNCTION ──────────────────────────────────────────────
def get_logged_in_organizer(cursor, user_id):

    cursor.execute(
        '''
        SELECT organizer_id
        FROM Organizers
        WHERE user_id = ?
        ''',
        (user_id,)
    )

    organizer = cursor.fetchone()

    if not organizer:

        raise HTTPException(
            status_code=403,
            detail="Organizer account not found"
        )

    return organizer.organizer_id


# ── VERIFY EVENT OWNERSHIP ───────────────────────────────────────
def verify_event_ownership(cursor, event_id, organizer_id):

    cursor.execute(
        '''
        SELECT *
        FROM HackathonEvents
        WHERE event_id = ?
          AND organizer_id = ?
        ''',
        (event_id, organizer_id)
    )

    event = cursor.fetchone()

    if not event:

        raise HTTPException(
            status_code=403,
            detail="Not your event"
        )

    return event


# ── VALIDATE REQUIRED FIELDS ─────────────────────────────────────
def validate_required_fields(data, required_fields):

    missing_fields = []

    for field in required_fields:

        if field not in data or data[field] in [None, ""]:

            missing_fields.append(field)

    if missing_fields:

        raise HTTPException(
            status_code=400,
            detail=f"Missing required fields: {', '.join(missing_fields)}"
        )


# ── Create event ──────────────────────────────────────────────────────────────
@router.post('/create-event')
async def create_event(
    request: Request,
    user = Depends(verify_token)
):

    if user["role"] != "organizer":

        raise HTTPException(
            status_code=403,
            detail="Organizers only"
        )

    data = await request.json()

    # ── VALIDATION ───────────────────────────────────────────────
    validate_required_fields(
        data,
        [
            "event_name",
            "start_date",
            "end_date",
            "last_date_of_registration",
            "max_team_size",
        ]
    )

    # ── DATE FORMAT & LOGIC CHECKS ───────────────────────────────
    try:

        start_date       = date.fromisoformat(data['start_date'])
        end_date         = date.fromisoformat(data['end_date'])
        last_date_of_reg = date.fromisoformat(data['last_date_of_registration'])

    except ValueError:

        raise HTTPException(
            status_code=400,
            detail="Invalid date format. Use YYYY-MM-DD."
        )

    if end_date < start_date:

        raise HTTPException(
            status_code=400,
            detail="end_date cannot be before start_date."
        )

    if last_date_of_reg > start_date:

        raise HTTPException(
            status_code=400,
            detail="last_date_of_registration must be on or before start_date."
        )

    # ── MAX TEAM SIZE CHECK ──────────────────────────────────────
    if not isinstance(data['max_team_size'], int) or data['max_team_size'] < 1:

        raise HTTPException(
            status_code=400,
            detail="max_team_size must be a positive integer."
        )

    conn   = get_connection()
    cursor = conn.cursor()

    organizer_id = get_logged_in_organizer(
        cursor,
        user["user_id"]
    )

    cursor.execute(
        '''
        INSERT INTO HackathonEvents
            (
                event_name,
                start_date,
                end_date,
                last_date_of_registration,
                max_team_size,
                event_details,
                organizer_id,
                budget,
                funding,
                first_prize,
                second_prize,
                third_prize,
                event_status
            )
        OUTPUT INSERTED.event_id
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',
        (
            data['event_name'],
            data['start_date'],
            data['end_date'],
            data['last_date_of_registration'],
            data['max_team_size'],
            data.get('event_details'),
            organizer_id,
            data.get('budget', 0),
            data.get('funding', 0),
            data.get('first_prize', 0),
            data.get('second_prize', 0),
            data.get('third_prize', 0),
            data.get('event_status', 'upcoming'),
        )
    )

    event_id = cursor.fetchone()[0]

    conn.commit()
    conn.close()

    return {
        'message': 'Event created successfully',
        'event_id': event_id
    }


# ── Update event status ───────────────────────────────────────────────────────
@router.put('/update-event-status')
async def update_event_status(
    request: Request,
    user = Depends(verify_token)
):

    if user["role"] != "organizer":

        raise HTTPException(
            status_code=403,
            detail="Organizers only"
        )

    data = await request.json()

    valid_statuses = (
        'upcoming',
        'ongoing',
        'completed'
    )

    if data['event_status'] not in valid_statuses:

        raise HTTPException(
            status_code=400,
            detail=f'Invalid status. Choose from: {valid_statuses}'
        )

    conn   = get_connection()
    cursor = conn.cursor()

    organizer_id = get_logged_in_organizer(
        cursor,
        user["user_id"]
    )

    verify_event_ownership(
        cursor,
        data["event_id"],
        organizer_id
    )

    cursor.execute(
        '''
        UPDATE HackathonEvents
        SET event_status = ?
        WHERE event_id = ?
        ''',
        (
            data['event_status'],
            data['event_id']
        )
    )

    conn.commit()
    conn.close()

    return {
        'message': 'Event status updated successfully'
    }


# ── View all events (organizer sees ONLY own) ───────────────────
@router.get('/my-events')
def my_events(user = Depends(verify_token)):

    if user["role"] != "organizer":

        raise HTTPException(
            status_code=403,
            detail="Organizers only"
        )

    conn   = get_connection()
    cursor = conn.cursor()

    organizer_id = get_logged_in_organizer(
        cursor,
        user["user_id"]
    )

    cursor.execute(
        '''
        SELECT event_id,
               event_name,
               start_date,
               end_date,
               last_date_of_registration,
               max_team_size,
               event_status,
               budget,
               funding,
               first_prize,
               second_prize,
               third_prize
        FROM HackathonEvents
        WHERE organizer_id = ?
        ORDER BY start_date DESC
        ''',
        (organizer_id,)
    )

    rows = cursor.fetchall()

    conn.close()

    return [
        {
            'event_id'                  : r.event_id,
            'event_name'                : r.event_name,
            'start_date'                : str(r.start_date),
            'end_date'                  : str(r.end_date),
            'last_date_of_registration' : str(r.last_date_of_registration),
            'max_team_size'             : r.max_team_size,
            'event_status'              : r.event_status,
            'budget'                    : float(r.budget),
            'funding'                   : float(r.funding),
            'first_prize'               : float(r.first_prize),
            'second_prize'              : float(r.second_prize),
            'third_prize'               : float(r.third_prize),
        }
        for r in rows
    ]


# ── View single event detail ────────────────────────────────────
@router.get('/event-detail/{event_id}')
def event_detail(
    event_id: int,
    user = Depends(verify_token)
):

    if user["role"] != "organizer":

        raise HTTPException(
            status_code=403,
            detail="Organizers only"
        )

    conn   = get_connection()
    cursor = conn.cursor()

    organizer_id = get_logged_in_organizer(
        cursor,
        user["user_id"]
    )

    verify_event_ownership(
        cursor,
        event_id,
        organizer_id
    )

    cursor.execute(
        '''
        SELECT *
        FROM HackathonEvents
        WHERE event_id = ?
        ''',
        (event_id,)
    )

    r = cursor.fetchone()

    conn.close()

    return {
        'event_id'                  : r.event_id,
        'event_name'                : r.event_name,
        'start_date'                : str(r.start_date),
        'end_date'                  : str(r.end_date),
        'last_date_of_registration' : str(r.last_date_of_registration),
        'max_team_size'             : r.max_team_size,
        'event_details'             : r.event_details,
        'organizer_id'              : r.organizer_id,
        'budget'                    : float(r.budget),
        'funding'                   : float(r.funding),
        'first_prize'               : float(r.first_prize),
        'second_prize'              : float(r.second_prize),
        'third_prize'               : float(r.third_prize),
        'event_status'              : r.event_status,
    }


# ── Assign judge ────────────────────────────────────────────────
@router.post('/assign-judge')
async def assign_judge(
    request: Request,
    user = Depends(verify_token)
):

    if user["role"] != "organizer":

        raise HTTPException(
            status_code=403,
            detail="Organizers only"
        )

    data = await request.json()

    conn   = get_connection()
    cursor = conn.cursor()

    organizer_id = get_logged_in_organizer(
        cursor,
        user["user_id"]
    )

    verify_event_ownership(
        cursor,
        data["event_id"],
        organizer_id
    )

    cursor.execute(
        '''
        INSERT INTO EventJudges
            (
                event_id,
                judge_id
            )
        VALUES (?, ?)
        ''',
        (
            data['event_id'],
            data['judge_id']
        )
    )

    conn.commit()
    conn.close()

    return {
        'message': 'Judge assigned successfully'
    }


# ── View event judges ───────────────────────────────────────────
@router.get('/event-judges/{event_id}')
def event_judges(
    event_id: int,
    user = Depends(verify_token)
):

    if user["role"] != "organizer":

        raise HTTPException(
            status_code=403,
            detail="Organizers only"
        )

    conn   = get_connection()
    cursor = conn.cursor()

    organizer_id = get_logged_in_organizer(
        cursor,
        user["user_id"]
    )

    verify_event_ownership(
        cursor,
        event_id,
        organizer_id
    )

    cursor.execute(
        '''
        SELECT
            j.judge_id,
            u.firstname,
            u.lastname,
            u.email,
            ej.assigned_date
        FROM EventJudges ej
        INNER JOIN Judges j
            ON ej.judge_id = j.judge_id
        INNER JOIN Users u
            ON j.user_id = u.user_id
        WHERE ej.event_id = ?
        ''',
        (event_id,)
    )

    rows = cursor.fetchall()

    conn.close()

    return [
        {
            'judge_id'      : r.judge_id,
            'name'          : r.firstname + ' ' + r.lastname,
            'email'         : r.email,
            'assigned_date' : str(r.assigned_date),
        }
        for r in rows
    ]


# ── View teams ──────────────────────────────────────────────────
@router.get('/event-teams/{event_id}')
def event_teams(
    event_id: int,
    user = Depends(verify_token)
):

    if user["role"] != "organizer":

        raise HTTPException(
            status_code=403,
            detail="Organizers only"
        )

    conn   = get_connection()
    cursor = conn.cursor()

    organizer_id = get_logged_in_organizer(
        cursor,
        user["user_id"]
    )

    verify_event_ownership(
        cursor,
        event_id,
        organizer_id
    )

    cursor.execute(
        '''
        SELECT
            t.team_id,
            t.team_name,
            t.team_code,
            t.registration_date,
            u.firstname,
            u.lastname
        FROM Teams t
        INNER JOIN Participants p
            ON t.team_lead = p.participant_id
        INNER JOIN Users u
            ON p.user_id = u.user_id
        WHERE t.event_id = ?
        ''',
        (event_id,)
    )

    rows = cursor.fetchall()

    conn.close()

    return [
        {
            'team_id'           : r.team_id,
            'team_name'         : r.team_name,
            'team_code'         : r.team_code,
            'registration_date' : str(r.registration_date),
            'team_lead'         : r.firstname + ' ' + r.lastname,
        }
        for r in rows
    ]


# ── View submitted projects ─────────────────────────────────────
@router.get('/submitted-projects/{event_id}')
def submitted_projects(
    event_id: int,
    user = Depends(verify_token)
):

    if user["role"] != "organizer":

        raise HTTPException(
            status_code=403,
            detail="Organizers only"
        )

    conn   = get_connection()
    cursor = conn.cursor()

    organizer_id = get_logged_in_organizer(
        cursor,
        user["user_id"]
    )

    verify_event_ownership(
        cursor,
        event_id,
        organizer_id
    )

    cursor.execute(
        '''
        SELECT
            p.project_id,
            p.project_name,
            p.status,
            p.github_link,
            p.submission_date,
            t.team_name
        FROM Projects p
        INNER JOIN Teams t
            ON p.team_id = t.team_id
        WHERE t.event_id = ?
        ''',
        (event_id,)
    )

    rows = cursor.fetchall()

    conn.close()

    return [
        {
            'project_id'      : r.project_id,
            'project_name'    : r.project_name,
            'team_name'       : r.team_name,
            'status'          : r.status,
            'github_link'     : r.github_link,
            'submission_date' : str(r.submission_date),
        }
        for r in rows
    ]


# ── View registrations ──────────────────────────────────────────
@router.get('/event-registrations/{event_id}')
def event_registrations(
    event_id: int,
    user = Depends(verify_token)
):

    if user["role"] != "organizer":

        raise HTTPException(
            status_code=403,
            detail="Organizers only"
        )

    conn   = get_connection()
    cursor = conn.cursor()

    organizer_id = get_logged_in_organizer(
        cursor,
        user["user_id"]
    )

    verify_event_ownership(
        cursor,
        event_id,
        organizer_id
    )

    cursor.execute(
        '''
        SELECT
            er.participant_id,
            er.registration_date,
            u.firstname,
            u.lastname,
            u.email
        FROM EventRegistrations er
        INNER JOIN Participants p
            ON er.participant_id = p.participant_id
        INNER JOIN Users u
            ON p.user_id = u.user_id
        WHERE er.event_id = ?
        ORDER BY er.registration_date
        ''',
        (event_id,)
    )

    rows = cursor.fetchall()

    conn.close()

    return [
        {
            'participant_id'    : r.participant_id,
            'name'              : r.firstname + ' ' + r.lastname,
            'email'             : r.email,
            'registration_date' : str(r.registration_date),
        }
        for r in rows
    ]


# ── Delete Team ─────────────────────────────────────────────────
@router.delete('/delete-team/{team_id}')
def delete_team(
    team_id: int,
    user = Depends(verify_token)
):

    if user["role"] != "organizer":

        raise HTTPException(
            status_code=403,
            detail="Organizers only"
        )

    conn   = get_connection()
    cursor = conn.cursor()

    organizer_id = get_logged_in_organizer(
        cursor,
        user["user_id"]
    )

    # Verify team belongs to organizer's event
    cursor.execute(
        '''
        SELECT t.team_id
        FROM Teams t
        INNER JOIN HackathonEvents h
            ON t.event_id = h.event_id
        WHERE t.team_id = ?
          AND h.organizer_id = ?
        ''',
        (
            team_id,
            organizer_id
        )
    )

    team = cursor.fetchone()

    if not team:

        raise HTTPException(
            status_code=403,
            detail="You cannot delete this team"
        )

    # Cascade (ON DELETE CASCADE) handles TeamMembers and Projects automatically
    cursor.execute(
        '''
        DELETE FROM Teams
        WHERE team_id = ?
        ''',
        (team_id,)
    )

    conn.commit()
    conn.close()

    return {
        "message": "Team deleted successfully"
    }