from fastapi import APIRouter, Depends, HTTPException
from app.database import get_connection
from app.routers.auth import verify_token
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter(prefix='/admin', tags=['Admin'])


# ── REQUEST MODELS ────────────────────────────────────────────────
class CreateJudgeRequest(BaseModel):
    cnic               : str
    firstname          : str
    middlename         : Optional[str]   = None
    lastname           : str
    email              : str
    password           : str
    commission_per_eval: float
    degrees            : Optional[List[str]] = []
    phone_numbers      : Optional[List[str]] = []


class CreateOrganizerRequest(BaseModel):
    cnic         : str
    firstname    : str
    middlename   : Optional[str]   = None
    lastname     : str
    email        : str
    password     : str
    salary       : Optional[float] = None
    phone_numbers: Optional[List[str]] = []


class UpdateJudgeRequest(BaseModel):
    firstname          : Optional[str]   = None
    middlename         : Optional[str]   = None
    lastname           : Optional[str]   = None
    email              : Optional[str]   = None
    password           : Optional[str]   = None
    commission_per_eval: Optional[float] = None
    degrees            : Optional[List[str]] = None
    phone_numbers      : Optional[List[str]] = None


class UpdateOrganizerRequest(BaseModel):
    firstname    : Optional[str]   = None
    middlename   : Optional[str]   = None
    lastname     : Optional[str]   = None
    email        : Optional[str]   = None
    password     : Optional[str]   = None
    salary       : Optional[float] = None
    phone_numbers: Optional[List[str]] = None


# ── HELPER DUPLICATE CHECK FUNCTION ─────────────────────────────
def check_duplicate_user(cursor, cnic, email):

    cursor.execute(
        '''
        SELECT
            CASE WHEN EXISTS (SELECT 1 FROM Users WHERE cnic  = ?) THEN 1 ELSE 0 END,
            CASE WHEN EXISTS (SELECT 1 FROM Users WHERE email = ?) THEN 1 ELSE 0 END
        ''',
        (cnic, email)
    )

    cnic_exists, email_exists = cursor.fetchone()

    if cnic_exists:
        raise HTTPException(
            status_code=400,
            detail="A user with this CNIC already exists"
        )

    if email_exists:
        raise HTTPException(
            status_code=400,
            detail="A user with this email already exists"
        )


# ── HELPER VALIDATION FUNCTION ──────────────────────────────────
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


# ── Create Judge ──────────────────────────────────────────────────────────────
@router.post('/create-judge')
async def create_judge(
    data: CreateJudgeRequest,
    user = Depends(verify_token)
):
    """
    Admin creates a judge account.

    Required:
        cnic, firstname, lastname,
        email, password,
        commission_per_eval

    Optional:
        middlename
        degrees (list)
        phone_numbers (list)
    """

    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admins only")

    conn   = get_connection()
    cursor = conn.cursor()

    try:

        check_duplicate_user(cursor, data.cnic, data.email)

        cursor.execute(
            '''
            INSERT INTO Users
                (cnic, firstname, middlename, lastname, email, password, role, created_at)
            OUTPUT INSERTED.user_id
            VALUES (?, ?, ?, ?, ?, ?, 'judge', GETDATE())
            ''',
            (data.cnic, data.firstname, data.middlename, data.lastname, data.email, data.password)
        )

        user_id = cursor.fetchone()[0]

        cursor.execute(
            '''
            INSERT INTO Judges (user_id, commission_per_eval)
            OUTPUT INSERTED.judge_id
            VALUES (?, ?)
            ''',
            (user_id, data.commission_per_eval)
        )

        judge_id = cursor.fetchone()[0]

        for degree in set(data.degrees or []):
            cursor.execute(
                'INSERT INTO Degrees (judge_id, degree) VALUES (?, ?)',
                (judge_id, degree)
            )

        for phone in set(data.phone_numbers or []):
            cursor.execute(
                'INSERT INTO Telephones (user_id, phone_number) VALUES (?, ?)',
                (user_id, phone)
            )

        conn.commit()

        return {
            'message' : 'Judge created successfully',
            'judge_id': judge_id
        }

    finally:
        conn.close()


# ── Create Organizer ──────────────────────────────────────────────────────────
@router.post('/create-organizer')
async def create_organizer(
    data: CreateOrganizerRequest,
    user = Depends(verify_token)
):
    """
    Admin creates an organizer account.

    Required:
        cnic, firstname, lastname,
        email, password

    Optional:
        middlename, salary, phone_numbers
    """

    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admins only")

    conn   = get_connection()
    cursor = conn.cursor()

    try:

        check_duplicate_user(cursor, data.cnic, data.email)

        cursor.execute(
            '''
            INSERT INTO Users
                (cnic, firstname, middlename, lastname, email, password, role, created_at)
            OUTPUT INSERTED.user_id
            VALUES (?, ?, ?, ?, ?, ?, 'organizer', GETDATE())
            ''',
            (data.cnic, data.firstname, data.middlename, data.lastname, data.email, data.password)
        )

        user_id = cursor.fetchone()[0]

        cursor.execute(
            '''
            INSERT INTO Organizers (user_id, salary)
            OUTPUT INSERTED.organizer_id
            VALUES (?, ?)
            ''',
            (user_id, data.salary)
        )

        organizer_id = cursor.fetchone()[0]

        for phone in set(data.phone_numbers or []):
            cursor.execute(
                'INSERT INTO Telephones (user_id, phone_number) VALUES (?, ?)',
                (user_id, phone)
            )

        conn.commit()

        return {
            'message'     : 'Organizer created successfully',
            'organizer_id': organizer_id
        }

    finally:
        conn.close()


# ── View All Users ────────────────────────────────────────────────────────────
@router.get('/users')
def all_users(user = Depends(verify_token)):

    """
    Admin can view all users.
    """

    # ── Only Admin Allowed ───────────────────────────────────────
    if user["role"] != "admin":

        raise HTTPException(
            status_code=403,
            detail="Admins only"
        )

    conn   = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        '''
        SELECT
            user_id,
            firstname,
            lastname,
            email,
            role
        FROM Users
        ORDER BY created_at DESC
        '''
    )

    rows = cursor.fetchall()

    conn.close()

    return [
        {
            'user_id'  : r.user_id,
            'firstname': r.firstname,
            'lastname' : r.lastname,
            'email'    : r.email,
            'role'     : r.role,
        }
        for r in rows
    ]


# ── View All Judges ───────────────────────────────────────────────────────────
@router.get('/judges')
def all_judges(user = Depends(verify_token)):

    """
    Admin can view all judges.
    """

    # ── Only Admin Allowed ───────────────────────────────────────
    if user["role"] != "admin":

        raise HTTPException(
            status_code=403,
            detail="Admins only"
        )

    conn   = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        '''
        SELECT
            j.judge_id,
            j.user_id,
            u.firstname,
            u.lastname,
            u.email,
            j.commission_per_eval
        FROM Judges j
        INNER JOIN Users u
            ON j.user_id = u.user_id
        '''
    )

    rows = cursor.fetchall()

    # ── Fetch all degrees keyed by judge_id ──────────────────────
    cursor.execute(
        '''
        SELECT d.judge_id, d.degree
        FROM Degrees d
        INNER JOIN Judges j ON j.judge_id = d.judge_id
        '''
    )

    degrees_map = {}
    for d in cursor.fetchall():
        degrees_map.setdefault(d.judge_id, []).append(d.degree)

    # ── Fetch judge phone numbers keyed by user_id ───────────────
    cursor.execute(
        '''
        SELECT t.user_id, t.phone_number
        FROM Telephones t
        INNER JOIN Judges j ON j.user_id = t.user_id
        '''
    )

    phones_map = {}
    for p in cursor.fetchall():
        phones_map.setdefault(p.user_id, []).append(p.phone_number)

    conn.close()

    return [
        {
            'judge_id'            : r.judge_id,
            'name'                : r.firstname + ' ' + r.lastname,
            'email'               : r.email,
            'commission_per_eval' : float(r.commission_per_eval),
            'degrees'             : degrees_map.get(r.judge_id, []),
            'phone_numbers'       : phones_map.get(r.user_id, [])
        }
        for r in rows
    ]


# ── View All Organizers ───────────────────────────────────────────────────────
@router.get('/organizers')
def all_organizers(user = Depends(verify_token)):

    """
    Admin can view all organizers.
    """

    # ── Only Admin Allowed ───────────────────────────────────────
    if user["role"] != "admin":

        raise HTTPException(
            status_code=403,
            detail="Admins only"
        )

    conn   = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        '''
        SELECT
            o.organizer_id,
            o.user_id,
            u.firstname,
            u.lastname,
            u.email,
            o.salary
        FROM Organizers o
        INNER JOIN Users u
            ON o.user_id = u.user_id
        '''
    )

    rows = cursor.fetchall()

    # ── Fetch organizer phone numbers keyed by user_id ───────────
    cursor.execute(
        '''
        SELECT t.user_id, t.phone_number
        FROM Telephones t
        INNER JOIN Organizers o ON o.user_id = t.user_id
        '''
    )

    phones_map = {}
    for p in cursor.fetchall():
        phones_map.setdefault(p.user_id, []).append(p.phone_number)

    conn.close()

    return [
        {
            'organizer_id' : r.organizer_id,
            'name'         : r.firstname + ' ' + r.lastname,
            'email'        : r.email,
            'salary'       : float(r.salary) if r.salary else None,
            'phone_numbers': phones_map.get(r.user_id, [])
        }
        for r in rows
    ]


# ── View All Events ───────────────────────────────────────────────────────────
@router.get('/events')
def all_events(user = Depends(verify_token)):

    """
    Admin can view all hackathon events.
    """

    # ── Only Admin Allowed ───────────────────────────────────────
    if user["role"] != "admin":

        raise HTTPException(
            status_code=403,
            detail="Admins only"
        )

    conn   = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        '''
        SELECT
            event_id,
            event_name,
            start_date,
            end_date,
            last_date_of_registration,
            max_team_size,
            organizer_id,
            budget,
            funding,
            first_prize,
            second_prize,
            third_prize,
            event_details,
            event_status
        FROM HackathonEvents
        ORDER BY start_date DESC
        '''
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
            'organizer_id'              : r.organizer_id,
            'budget'                    : float(r.budget),
            'funding'                   : float(r.funding),
            'first_prize'               : float(r.first_prize),
            'second_prize'              : float(r.second_prize),
            'third_prize'               : float(r.third_prize),
            'event_details'             : r.event_details,
            'event_status'              : r.event_status
        }
        for r in rows
    ]


# ── View Single User Detail ───────────────────────────────────────────────────
@router.get('/users/{user_id}')
def user_detail(
    user_id: int,
    user = Depends(verify_token)
):
    """
    Admin can view full details of a single user.
    Returns role-specific data (participant/judge/organizer fields).
    """

    # ── Only Admin Allowed ───────────────────────────────────────
    if user["role"] != "admin":

        raise HTTPException(
            status_code=403,
            detail="Admins only"
        )

    conn   = get_connection()
    cursor = conn.cursor()

    # ── Fetch base user ──────────────────────────────────────────
    cursor.execute(
        '''
        SELECT
            user_id,
            cnic,
            firstname,
            middlename,
            lastname,
            email,
            role,
            created_at
        FROM Users
        WHERE user_id = ?
        ''',
        (user_id,)
    )

    row = cursor.fetchone()

    if not row:
        conn.close()
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # ── Fetch phone numbers ──────────────────────────────────────
    cursor.execute(
        'SELECT phone_number FROM Telephones WHERE user_id = ?',
        (user_id,)
    )

    phones = [r.phone_number for r in cursor.fetchall()]

    # ── Build base response ──────────────────────────────────────
    result = {
        'user_id'   : row.user_id,
        'cnic'      : row.cnic,
        'firstname' : row.firstname,
        'middlename': row.middlename,
        'lastname'  : row.lastname,
        'email'     : row.email,
        'role'      : row.role,
        'created_at': str(row.created_at),
        'phone_numbers': phones
    }

    # ── Participant-specific data ────────────────────────────────
    if row.role == 'participant':

        cursor.execute(
            '''
            SELECT
                participant_id,
                date_of_birth,
                city,
                institution
            FROM Participants
            WHERE user_id = ?
            ''',
            (user_id,)
        )

        p = cursor.fetchone()

        if p:
            result['participant_id'] = p.participant_id
            result['date_of_birth']  = str(p.date_of_birth) if p.date_of_birth else None
            result['city']           = p.city
            result['institution']    = p.institution

    # ── Judge-specific data ──────────────────────────────────────
    elif row.role == 'judge':

        cursor.execute(
            '''
            SELECT
                judge_id,
                commission_per_eval
            FROM Judges
            WHERE user_id = ?
            ''',
            (user_id,)
        )

        j = cursor.fetchone()

        if j:
            cursor.execute(
                'SELECT degree FROM Degrees WHERE judge_id = ?',
                (j.judge_id,)
            )

            result['judge_id']            = j.judge_id
            result['commission_per_eval'] = float(j.commission_per_eval)
            result['degrees']             = [d.degree for d in cursor.fetchall()]

    # ── Organizer-specific data ──────────────────────────────────
    elif row.role == 'organizer':

        cursor.execute(
            '''
            SELECT
                organizer_id,
                salary
            FROM Organizers
            WHERE user_id = ?
            ''',
            (user_id,)
        )

        o = cursor.fetchone()

        if o:
            result['organizer_id'] = o.organizer_id
            result['salary']       = float(o.salary) if o.salary else None

    conn.close()

    return result


# ── Update Judge ──────────────────────────────────────────────────────────────
@router.put('/update-judge/{judge_id}')
async def update_judge(
    judge_id: int,
    data: UpdateJudgeRequest,
    user = Depends(verify_token)
):
    """
    Admin updates a judge's details.
    Only fields provided (non-None) are updated.
    judge_id cannot be changed.

    Updatable:
        firstname, middlename, lastname,
        email, password,
        commission_per_eval,
        degrees (replaces existing list),
        phone_numbers (replaces existing list)
    """

    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admins only")

    conn   = get_connection()
    cursor = conn.cursor()

    try:

        # Verify judge exists and get user_id
        cursor.execute(
            'SELECT user_id FROM Judges WHERE judge_id = ?',
            (judge_id,)
        )
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Judge not found")

        judge_user_id = row.user_id

        # ── Update Users table ───────────────────────────────────
        user_fields = {}
        if data.firstname   is not None: user_fields['firstname']  = data.firstname
        if data.middlename  is not None: user_fields['middlename'] = data.middlename
        if data.lastname    is not None: user_fields['lastname']   = data.lastname
        if data.password    is not None: user_fields['password']   = data.password

        if data.email is not None:
            # Check email not taken by another user
            cursor.execute(
                'SELECT 1 FROM Users WHERE email = ? AND user_id != ?',
                (data.email, judge_user_id)
            )
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="Email already in use")
            user_fields['email'] = data.email

        if user_fields:
            set_clause = ', '.join(f"{k} = ?" for k in user_fields)
            cursor.execute(
                f'UPDATE Users SET {set_clause} WHERE user_id = ?',
                (*user_fields.values(), judge_user_id)
            )

        # ── Update Judges table ──────────────────────────────────
        if data.commission_per_eval is not None:
            if data.commission_per_eval < 0:
                raise HTTPException(status_code=400, detail="commission_per_eval cannot be negative")
            cursor.execute(
                'UPDATE Judges SET commission_per_eval = ? WHERE judge_id = ?',
                (data.commission_per_eval, judge_id)
            )

        # ── Replace degrees if provided ──────────────────────────
        if data.degrees is not None:
            cursor.execute('DELETE FROM Degrees WHERE judge_id = ?', (judge_id,))
            for degree in set(data.degrees):
                cursor.execute(
                    'INSERT INTO Degrees (judge_id, degree) VALUES (?, ?)',
                    (judge_id, degree)
                )

        # ── Replace phone numbers if provided ────────────────────
        if data.phone_numbers is not None:
            cursor.execute('DELETE FROM Telephones WHERE user_id = ?', (judge_user_id,))
            for phone in set(data.phone_numbers):
                cursor.execute(
                    'INSERT INTO Telephones (user_id, phone_number) VALUES (?, ?)',
                    (judge_user_id, phone)
                )

        conn.commit()

        return {'message': 'Judge updated successfully'}

    finally:
        conn.close()


# ── Update Organizer ──────────────────────────────────────────────────────────
@router.put('/update-organizer/{organizer_id}')
async def update_organizer(
    organizer_id: int,
    data: UpdateOrganizerRequest,
    user = Depends(verify_token)
):
    """
    Admin updates an organizer's details.
    Only fields provided (non-None) are updated.
    organizer_id cannot be changed.

    Updatable:
        firstname, middlename, lastname,
        email, password,
        salary,
        phone_numbers (replaces existing list)
    """

    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admins only")

    conn   = get_connection()
    cursor = conn.cursor()

    try:

        # Verify organizer exists and get user_id
        cursor.execute(
            'SELECT user_id FROM Organizers WHERE organizer_id = ?',
            (organizer_id,)
        )
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Organizer not found")

        org_user_id = row.user_id

        # ── Update Users table ───────────────────────────────────
        user_fields = {}
        if data.firstname  is not None: user_fields['firstname']  = data.firstname
        if data.middlename is not None: user_fields['middlename'] = data.middlename
        if data.lastname   is not None: user_fields['lastname']   = data.lastname
        if data.password   is not None: user_fields['password']   = data.password

        if data.email is not None:
            cursor.execute(
                'SELECT 1 FROM Users WHERE email = ? AND user_id != ?',
                (data.email, org_user_id)
            )
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="Email already in use")
            user_fields['email'] = data.email

        if user_fields:
            set_clause = ', '.join(f"{k} = ?" for k in user_fields)
            cursor.execute(
                f'UPDATE Users SET {set_clause} WHERE user_id = ?',
                (*user_fields.values(), org_user_id)
            )

        # ── Update Organizers table ──────────────────────────────
        if data.salary is not None:
            if data.salary < 0:
                raise HTTPException(status_code=400, detail="Salary cannot be negative")
            cursor.execute(
                'UPDATE Organizers SET salary = ? WHERE organizer_id = ?',
                (data.salary, organizer_id)
            )

        # ── Replace phone numbers if provided ────────────────────
        if data.phone_numbers is not None:
            cursor.execute('DELETE FROM Telephones WHERE user_id = ?', (org_user_id,))
            for phone in set(data.phone_numbers):
                cursor.execute(
                    'INSERT INTO Telephones (user_id, phone_number) VALUES (?, ?)',
                    (org_user_id, phone)
                )

        conn.commit()

        return {'message': 'Organizer updated successfully'}

    finally:
        conn.close()


# ── Delete User ───────────────────────────────────────────────────────────────
@router.delete('/delete-user/{user_id}')
def delete_user(
    user_id: int,
    user = Depends(verify_token)
):

    """
    Admin deletes a user.
    Related records delete automatically because of CASCADE.
    """

    # ── Only Admin Allowed ───────────────────────────────────────
    if user["role"] != "admin":

        raise HTTPException(
            status_code=403,
            detail="Admins only"
        )

    conn   = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        '''
        DELETE FROM Users
        WHERE user_id = ?
        ''',
        (user_id,)
    )

    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    conn.commit()
    conn.close()

    return {
        'message': 'User deleted successfully'
    }