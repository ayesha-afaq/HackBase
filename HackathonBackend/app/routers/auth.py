from fastapi import APIRouter, Request, HTTPException, Header
from app.database import get_connection
from jose import jwt, JWTError
from datetime import datetime, timedelta

router = APIRouter(prefix='/auth', tags=['Authentication'])

# ── JWT SETTINGS ─────────────────────────────────────────────────
SECRET_KEY = "MYSECRETKEY"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 5


# ── CREATE JWT TOKEN ─────────────────────────────────────────────
def create_access_token(data: dict):

    payload = data.copy()

    payload["exp"] = datetime.utcnow() + timedelta(
        hours=ACCESS_TOKEN_EXPIRE_HOURS
    )

    token = jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return token


# ── VERIFY JWT TOKEN ─────────────────────────────────────────────
def verify_token(authorization: str = Header(None)):

    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Token missing"
        )

    try:

        token = authorization.split(" ")[1]

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        return payload

    except JWTError:

        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )


# ── REGISTER (Participant only) ─────────────────────────────────
@router.post('/register')
async def register(request: Request):
    """
    Sign-up endpoint.
    Anyone who registers becomes a Participant.

    Required:
        cnic, firstname, lastname,
        email, password,
        date_of_birth, city, institution

    Optional:
        middlename
        phone_numbers (list)
    """

    data = await request.json()

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
        VALUES (?, ?, ?, ?, ?, ?, 'participant', GETDATE())
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

    # Insert into Participants
    cursor.execute(
        '''
        INSERT INTO Participants
            (
                user_id,
                date_of_birth,
                city,
                institution
            )
        VALUES (?, ?, ?, ?)
        ''',
        (
            user_id,
            data.get('date_of_birth'),
            data.get('city'),
            data.get('institution'),
        )
    )

    # Insert phone numbers
    for phone in data.get('phone_numbers', []):

        cursor.execute(
            '''
            INSERT INTO Telephones
                (user_id, phone_number)
            VALUES (?, ?)
            ''',
            (user_id, phone)
        )

    conn.commit()
    conn.close()

    return {
        'message': 'Registered successfully. You can now log in.'
    }


# ── LOGIN ────────────────────────────────────────────────────────
@router.post('/login')
async def login(request: Request):
    """
    Login using email + password.

    Returns:
        token (JWT — includes user_id, role, and the role-specific ID)
        role
        user_id
        participant_id / judge_id / organizer_id
    """

    data = await request.json()

    conn   = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        '''
        SELECT user_id,
               firstname,
               lastname,
               role
        FROM Users
        WHERE email = ?
          AND password = ?
        ''',
        (
            data['email'],
            data['password']
        )
    )

    user = cursor.fetchone()

    conn.close()

    if not user:

        raise HTTPException(
            status_code=401,
            detail='Invalid email or password'
        )

    extra = {}

    # ── Participant ID ───────────────────────────────────────────
    if user.role == 'participant':

        conn2   = get_connection()
        cursor2 = conn2.cursor()

        cursor2.execute(
            '''
            SELECT participant_id
            FROM Participants
            WHERE user_id = ?
            ''',
            (user.user_id,)
        )

        row = cursor2.fetchone()

        conn2.close()

        if row:
            extra['participant_id'] = row.participant_id

    # ── Judge ID ─────────────────────────────────────────────────
    if user.role == 'judge':

        conn2   = get_connection()
        cursor2 = conn2.cursor()

        cursor2.execute(
            '''
            SELECT judge_id
            FROM Judges
            WHERE user_id = ?
            ''',
            (user.user_id,)
        )

        row = cursor2.fetchone()

        conn2.close()

        if row:
            extra['judge_id'] = row.judge_id

    # ── Organizer ID ─────────────────────────────────────────────
    if user.role == 'organizer':

        conn2   = get_connection()
        cursor2 = conn2.cursor()

        cursor2.execute(
            '''
            SELECT organizer_id
            FROM Organizers
            WHERE user_id = ?
            ''',
            (user.user_id,)
        )

        row = cursor2.fetchone()

        conn2.close()

        if row:
            extra['organizer_id'] = row.organizer_id

    # ── CREATE JWT TOKEN ─────────────────────────────────────────
    # FIX: include the role-specific ID inside the JWT payload so that
    # backend route handlers can read it via verify_token without an
    # extra DB query.
    token_payload = {
        "user_id": user.user_id,
        "role": user.role,
        **extra          # participant_id / judge_id / organizer_id
    }

    token = create_access_token(token_payload)

    return {
        'message' : 'Login successful',
        'token'   : token,
        'user_id' : user.user_id,
        'name'    : user.firstname + ' ' + user.lastname,
        'role'    : user.role,
        **extra
    }