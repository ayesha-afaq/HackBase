from fastapi import APIRouter, Request, Depends, HTTPException
from app.database import get_connection
from app.routers.auth import verify_token
from datetime import date
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix='/organizer', tags=['Organizer'])


# ── REQUEST MODELS ────────────────────────────────────────────────
class CreateEventRequest(BaseModel):
    event_name                : str
    start_date                : str
    end_date                  : str
    last_date_of_registration : str
    max_team_size             : int
    event_details             : Optional[str]   = None
    budget                    : Optional[float] = 0
    funding                   : Optional[float] = 0
    first_prize               : Optional[float] = 0
    second_prize              : Optional[float] = 0
    third_prize               : Optional[float] = 0
    event_status              : Optional[str]   = 'upcoming'


class UpdateEventStatusRequest(BaseModel):
    event_id    : int
    event_status: str


class UpdateEventRequest(BaseModel):
    event_name                : Optional[str]   = None
    last_date_of_registration : Optional[str]   = None
    max_team_size             : Optional[int]   = None
    event_details             : Optional[str]   = None
    budget                    : Optional[float] = None
    funding                   : Optional[float] = None
    first_prize               : Optional[float] = None
    second_prize              : Optional[float] = None
    third_prize               : Optional[float] = None
    event_status              : Optional[str]   = None


class AssignJudgeRequest(BaseModel):
    event_id: int
    judge_id: int


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
    data: CreateEventRequest,
    user = Depends(verify_token)
):

    if user["role"] != "organizer":
        raise HTTPException(status_code=403, detail="Organizers only")

    try:
        start_date       = date.fromisoformat(data.start_date)
        end_date         = date.fromisoformat(data.end_date)
        last_date_of_reg = date.fromisoformat(data.last_date_of_registration)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    if end_date < start_date:
        raise HTTPException(status_code=400, detail="end_date cannot be before start_date.")

    if last_date_of_reg > start_date:
        raise HTTPException(status_code=400, detail="last_date_of_registration must be on or before start_date.")

    if data.max_team_size < 1:
        raise HTTPException(status_code=400, detail="max_team_size must be a positive integer.")

    conn   = get_connection()
    cursor = conn.cursor()

    try:

        organizer_id = get_logged_in_organizer(cursor, user["user_id"])

        cursor.execute(
            '''
            INSERT INTO HackathonEvents
                (event_name, start_date, end_date, last_date_of_registration,
                 max_team_size, event_details, organizer_id, budget, funding,
                 first_prize, second_prize, third_prize, event_status)
            OUTPUT INSERTED.event_id
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                data.event_name, data.start_date, data.end_date,
                data.last_date_of_registration, data.max_team_size,
                data.event_details, organizer_id, data.budget, data.funding,
                data.first_prize, data.second_prize, data.third_prize,
                data.event_status,
            )
        )

        event_id = cursor.fetchone()[0]
        conn.commit()

        return {
            'message' : 'Event created successfully',
            'event_id': event_id
        }

    finally:
        conn.close()


# ── Update event ──────────────────────────────────────────────────────────────
@router.put('/update-event/{event_id}')
async def update_event(
    event_id: int,
    data: UpdateEventRequest,
    user = Depends(verify_token)
):
    """
    Organizer updates their own event.

    Cannot change: event_id, organizer_id, start_date, end_date.

    Updatable:
        event_name, last_date_of_registration, max_team_size,
        event_details, budget, funding,
        first_prize, second_prize, third_prize, event_status

    Validations:
        - last_date_of_registration must be <= start_date
        - max_team_size must be >= 1
        - budget, funding, prizes must be >= 0
        - event_status must be one of: upcoming, ongoing, completed
    """

    if user["role"] != "organizer":
        raise HTTPException(status_code=403, detail="Organizers only")

    conn   = get_connection()
    cursor = conn.cursor()

    try:

        organizer_id = get_logged_in_organizer(cursor, user["user_id"])

        # Verify ownership and fetch current event dates for validation
        cursor.execute(
            '''
            SELECT start_date, end_date
            FROM HackathonEvents
            WHERE event_id = ? AND organizer_id = ?
            ''',
            (event_id, organizer_id)
        )

        event = cursor.fetchone()

        if not event:
            raise HTTPException(status_code=403, detail="Not your event or event not found")

        current_start = event.start_date
        current_end   = event.end_date

        # ── Validate provided fields ─────────────────────────────
        if data.last_date_of_registration is not None:
            try:
                reg_date = date.fromisoformat(data.last_date_of_registration)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid last_date_of_registration format. Use YYYY-MM-DD."
                )
            if reg_date > current_start:
                raise HTTPException(
                    status_code=400,
                    detail="last_date_of_registration must be on or before start_date."
                )
            if reg_date > current_end:
                raise HTTPException(
                    status_code=400,
                    detail="last_date_of_registration cannot be after end_date."
                )

        if data.max_team_size is not None and data.max_team_size < 1:
            raise HTTPException(
                status_code=400,
                detail="max_team_size must be at least 1."
            )

        for field_name, value in [
            ('budget',       data.budget),
            ('funding',      data.funding),
            ('first_prize',  data.first_prize),
            ('second_prize', data.second_prize),
            ('third_prize',  data.third_prize),
        ]:
            if value is not None and value < 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"{field_name} cannot be negative."
                )

        if data.event_status is not None:
            valid_statuses = ('upcoming', 'ongoing', 'completed')
            if data.event_status not in valid_statuses:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid event_status. Choose from: {valid_statuses}"
                )

        if data.event_name is not None and not data.event_name.strip():
            raise HTTPException(
                status_code=400,
                detail="event_name cannot be empty."
            )

        # ── Build dynamic UPDATE ─────────────────────────────────
        fields = {}
        if data.event_name                is not None: fields['event_name']                = data.event_name.strip()
        if data.last_date_of_registration is not None: fields['last_date_of_registration'] = data.last_date_of_registration
        if data.max_team_size             is not None: fields['max_team_size']             = data.max_team_size
        if data.event_details             is not None: fields['event_details']             = data.event_details
        if data.budget                    is not None: fields['budget']                    = data.budget
        if data.funding                   is not None: fields['funding']                   = data.funding
        if data.first_prize               is not None: fields['first_prize']               = data.first_prize
        if data.second_prize              is not None: fields['second_prize']              = data.second_prize
        if data.third_prize               is not None: fields['third_prize']               = data.third_prize
        if data.event_status              is not None: fields['event_status']              = data.event_status

        if not fields:
            raise HTTPException(
                status_code=400,
                detail="No fields provided to update."
            )

        set_clause = ', '.join(f"{k} = ?" for k in fields)

        cursor.execute(
            f'UPDATE HackathonEvents SET {set_clause} WHERE event_id = ?',
            (*fields.values(), event_id)
        )

        conn.commit()

        return {'message': 'Event updated successfully'}

    finally:
        conn.close()


# ── Update event status ───────────────────────────────────────────────────────
@router.put('/update-event-status')
async def update_event_status(
    data: UpdateEventStatusRequest,
    user = Depends(verify_token)
):

    if user["role"] != "organizer":
        raise HTTPException(status_code=403, detail="Organizers only")

    valid_statuses = ('upcoming', 'ongoing', 'completed')

    if data.event_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f'Invalid status. Choose from: {valid_statuses}')

    conn   = get_connection()
    cursor = conn.cursor()

    try:

        organizer_id = get_logged_in_organizer(cursor, user["user_id"])
        verify_event_ownership(cursor, data.event_id, organizer_id)

        cursor.execute(
            'UPDATE HackathonEvents SET event_status = ? WHERE event_id = ?',
            (data.event_status, data.event_id)
        )

        conn.commit()

        return {'message': 'Event status updated successfully'}

    finally:
        conn.close()


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

    try:

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
                   event_status
            FROM HackathonEvents
            WHERE organizer_id = ?
            ORDER BY start_date DESC
            ''',
            (organizer_id,)
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

    finally:

        conn.close()


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

    try:

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

    finally:

        conn.close()


# ── Assign judge ────────────────────────────────────────────────
@router.post('/assign-judge')
async def assign_judge(
    data: AssignJudgeRequest,
    user = Depends(verify_token)
):

    if user["role"] != "organizer":
        raise HTTPException(status_code=403, detail="Organizers only")

    conn   = get_connection()
    cursor = conn.cursor()

    try:

        organizer_id = get_logged_in_organizer(cursor, user["user_id"])
        verify_event_ownership(cursor, data.event_id, organizer_id)

        cursor.execute('SELECT judge_id FROM Judges WHERE judge_id = ?', (data.judge_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=400, detail="Judge not found")

        cursor.execute(
            'SELECT 1 FROM EventJudges WHERE event_id = ? AND judge_id = ?',
            (data.event_id, data.judge_id)
        )
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Judge is already assigned to this event")

        cursor.execute(
            'INSERT INTO EventJudges (event_id, judge_id) VALUES (?, ?)',
            (data.event_id, data.judge_id)
        )

        conn.commit()

        return {'message': 'Judge assigned successfully'}

    finally:
        conn.close()


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

    try:

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

        return [
            {
                'judge_id'      : r.judge_id,
                'name'          : r.firstname + ' ' + r.lastname,
                'email'         : r.email,
                'assigned_date' : str(r.assigned_date),
            }
            for r in rows
        ]

    finally:

        conn.close()


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

    try:

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

    finally:

        conn.close()


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

    try:

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

    finally:

        conn.close()


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

    try:

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

        return [
            {
                'participant_id'    : r.participant_id,
                'name'              : r.firstname + ' ' + r.lastname,
                'email'             : r.email,
                'registration_date' : str(r.registration_date),
            }
            for r in rows
        ]

    finally:

        conn.close()


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

    try:

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

        return {
            "message": "Team deleted successfully"
        }

    finally:

        conn.close()