from fastapi import APIRouter, Request, Depends, HTTPException
from app.database import get_connection
from app.routers.auth import verify_token

router = APIRouter(prefix='/admin', tags=['Admin'])


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
    for degree in data.get('degrees', []):

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
    for phone in data.get('phone_numbers', []):

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
    conn.close()

    return {
        'message': 'Judge created successfully',
        'judge_id': judge_id
    }


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

    # Insert phone numbers
    for phone in data.get('phone_numbers', []):

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
    conn.close()

    return {
        'message': 'Organizer created successfully',
        'organizer_id': organizer_id
    }


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

    conn.close()

    return [
        {
            'judge_id'            : r.judge_id,
            'name'                : r.firstname + ' ' + r.lastname,
            'email'               : r.email,
            'commission_per_eval' : float(r.commission_per_eval)
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

    conn.close()

    return [
        {
            'organizer_id' : r.organizer_id,
            'name'         : r.firstname + ' ' + r.lastname,
            'email'        : r.email,
            'salary'       : float(r.salary) if r.salary else None
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
            event_status
        FROM HackathonEvents
        ORDER BY start_date DESC
        '''
    )

    rows = cursor.fetchall()

    conn.close()

    return [
        {
            'event_id'     : r.event_id,
            'event_name'   : r.event_name,
            'start_date'   : str(r.start_date),
            'end_date'     : str(r.end_date),
            'event_status' : r.event_status
        }
        for r in rows
    ]


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

    conn.commit()
    conn.close()

    return {
        'message': 'User deleted successfully'
    }