from fastapi import APIRouter, Request, Depends, HTTPException
from app.database import get_connection
from app.routers.auth import verify_token

router = APIRouter(prefix='/admin', tags=['Admin'])


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
    request: Request,
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

    # ── Only Admin Allowed ───────────────────────────────────────
    if user["role"] != "admin":

        raise HTTPException(
            status_code=403,
            detail="Admins only"
        )

    data = await request.json()

    # ── VALIDATION ───────────────────────────────────────────────
    validate_required_fields(
        data,
        [
            "cnic",
            "firstname",
            "lastname",
            "email",
            "password",
            "commission_per_eval"
        ]
    )

    conn   = get_connection()
    cursor = conn.cursor()

    try:

        # ── DUPLICATE CHECK ──────────────────────────────────────────
        check_duplicate_user(cursor, data['cnic'], data['email'])

        # Insert into Users
        cursor.execute(
            '''
            INSERT INTO Users
                (
                    cnic,
                    firstname,
                    middlename,
                    lastname,
                    email,
                    password,
                    role,
                    created_at
                )
            OUTPUT INSERTED.user_id
            VALUES (?, ?, ?, ?, ?, ?, 'judge', GETDATE())
            ''',
            (
                data['cnic'],
                data['firstname'],
                data.get('middlename'),
                data['lastname'],
                data['email'],
                data['password'],
            )
        )

        user_id = cursor.fetchone()[0]

        # Insert into Judges table
        cursor.execute(
            '''
            INSERT INTO Judges
                (
                    user_id,
                    commission_per_eval
                )
            OUTPUT INSERTED.judge_id
            VALUES (?, ?)
            ''',
            (
                user_id,
                data['commission_per_eval']
            )
        )

        judge_id = cursor.fetchone()[0]

        # Insert Degrees
        for degree in set(data.get('degrees', [])):

            cursor.execute(
                '''
                INSERT INTO Degrees
                    (
                        judge_id,
                        degree
                    )
                VALUES (?, ?)
                ''',
                (
                    judge_id,
                    degree
                )
            )

        # Insert Phone Numbers
        for phone in set(data.get('phone_numbers', [])):

            cursor.execute(
                '''
                INSERT INTO Telephones
                    (
                        user_id,
                        phone_number
                    )
                VALUES (?, ?)
                ''',
                (
                    user_id,
                    phone
                )
            )

        conn.commit()

        return {
            'message': 'Judge created successfully',
            'judge_id': judge_id
        }

    finally:

        conn.close()


# ── Create Organizer ──────────────────────────────────────────────────────────
@router.post('/create-organizer')
async def create_organizer(
    request: Request,
    user = Depends(verify_token)
):
    """
    Admin creates an organizer account.

    Required:
        cnic, firstname, lastname,
        email, password

    Optional:
        middlename
        salary
        phone_numbers
    """

    # ── Only Admin Allowed ───────────────────────────────────────
    if user["role"] != "admin":

        raise HTTPException(
            status_code=403,
            detail="Admins only"
        )

    data = await request.json()

    # ── VALIDATION ───────────────────────────────────────────────
    validate_required_fields(
        data,
        [
            "cnic",
            "firstname",
            "lastname",
            "email",
            "password"
        ]
    )

    conn   = get_connection()
    cursor = conn.cursor()

    try:

        # ── DUPLICATE CHECK ──────────────────────────────────────────
        check_duplicate_user(cursor, data['cnic'], data['email'])

        # Insert into Users
        cursor.execute(
            '''
            INSERT INTO Users
                (
                    cnic,
                    firstname,
                    middlename,
                    lastname,
                    email,
                    password,
                    role,
                    created_at
                )
            OUTPUT INSERTED.user_id
            VALUES (?, ?, ?, ?, ?, ?, 'organizer', GETDATE())
            ''',
            (
                data['cnic'],
                data['firstname'],
                data.get('middlename'),
                data['lastname'],
                data['email'],
                data['password'],
            )
        )

        user_id = cursor.fetchone()[0]

        # Insert into Organizers
        cursor.execute(
            '''
            INSERT INTO Organizers
                (
                    user_id,
                    salary
                )
            OUTPUT INSERTED.organizer_id
            VALUES (?, ?)
            ''',
            (
                user_id,
                data.get('salary')
            )
        )

        organizer_id = cursor.fetchone()[0]

        # Insert phone numbers (deduplicated)
        for phone in set(data.get('phone_numbers', [])):

            cursor.execute(
                '''
                INSERT INTO Telephones
                    (
                        user_id,
                        phone_number
                    )
                VALUES (?, ?)
                ''',
                (
                    user_id,
                    phone
                )
            )

        conn.commit()

        return {
            'message': 'Organizer created successfully',
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
            cnic,
            firstname,
            lastname,
            email,
            role,
            created_at
        FROM Users
        ORDER BY created_at DESC
        '''
    )

    rows = cursor.fetchall()

    conn.close()

    return [
        {
            'user_id'   : r.user_id,
            'cnic'      : r.cnic,
            'name'      : r.firstname + ' ' + r.lastname,
            'email'     : r.email,
            'role'      : r.role,
            'created_at': str(r.created_at),
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