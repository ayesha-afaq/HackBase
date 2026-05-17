from fastapi import APIRouter, HTTPException, Header
from app.database import get_connection
from jose import jwt, JWTError
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter(prefix='/auth', tags=['Authentication'])

# ── JWT SETTINGS ─────────────────────────────────────────────────
SECRET_KEY = "MYSECRETKEY"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 5


# ── REQUEST MODELS ────────────────────────────────────────────────
class LoginRequest(BaseModel):
    email   : str
    password: str


class RegisterRequest(BaseModel):
    cnic          : str
    firstname     : str
    middlename    : Optional[str] = None
    lastname      : str
    email         : str
    password      : str
    date_of_birth : Optional[str] = None
    city          : Optional[str] = None
    institution   : Optional[str] = None
    phone_numbers : Optional[List[str]] = []


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

    parts = authorization.split(" ")

    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization format. Expected: Bearer <token>"
        )

    try:

        payload = jwt.decode(
            parts[1],
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
async def register(data: RegisterRequest):
    """
    Sign-up endpoint.
    Anyone who registers becomes a Participant.

    Required:
        cnic, firstname, lastname,
        email, password

    Optional:
        middlename
        date_of_birth, city, institution
        phone_numbers (list)
    """

    # ── Validate required fields ─────────────────────────────────
    required = ['cnic', 'firstname', 'lastname', 'email', 'password']
    missing  = [f for f in required if not getattr(data, f)]

    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required fields: {', '.join(missing)}"
        )

    conn   = get_connection()
    cursor = conn.cursor()

    try:

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
                data.cnic,
                data.firstname,
                data.middlename,
                data.lastname,
                data.email,
                data.password,
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
                data.date_of_birth,
                data.city,
                data.institution,
            )
        )

        # Insert phone numbers
        for phone in set(data.phone_numbers or []):

            cursor.execute(
                '''
                INSERT INTO Telephones
                    (user_id, phone_number)
                VALUES (?, ?)
                ''',
                (user_id, phone)
            )

        conn.commit()

    except HTTPException:
        conn.rollback()
        raise

    except Exception as e:
        conn.rollback()
        err = str(e)
        if '2627' in err or '2601' in err or 'UNIQUE' in err.upper():
            raise HTTPException(
                status_code=409,
                detail="An account with this CNIC or email already exists"
            )
        raise HTTPException(status_code=500, detail=err)

    finally:
        conn.close()

    return {
        'success': True,
        'message': 'Registered successfully. You can now log in.'
    }


# ── LOGIN ────────────────────────────────────────────────────────
@router.post('/login')
async def login(data: LoginRequest):
    """
    Login using email + password.

    Returns:
        token (JWT — includes user_id, role, and the role-specific ID)
        role
        user_id
        participant_id / judge_id / organizer_id
    """

    if not data.email or not data.password:
        raise HTTPException(
            status_code=400,
            detail="email and password are required"
        )

    conn   = get_connection()
    cursor = conn.cursor()

    try:

        # Single query: fetch user + role-specific ID via LEFT JOINs
        cursor.execute(
            '''
            SELECT
                u.user_id,
                u.firstname,
                u.lastname,
                u.role,
                p.participant_id,
                j.judge_id,
                o.organizer_id
            FROM Users u
            LEFT JOIN Participants p ON p.user_id = u.user_id
            LEFT JOIN Judges       j ON j.user_id = u.user_id
            LEFT JOIN Organizers   o ON o.user_id = u.user_id
            WHERE u.email    = ?
              AND u.password = ?
            ''',
            (data.email, data.password)
        )

        user = cursor.fetchone()

    finally:
        conn.close()

    if not user:
        raise HTTPException(
            status_code=401,
            detail='Invalid email or password'
        )

    # Build role-specific extra fields
    extra = {}

    if user.role == 'participant' and user.participant_id:
        extra['participant_id'] = user.participant_id

    elif user.role == 'judge' and user.judge_id:
        extra['judge_id'] = user.judge_id

    elif user.role == 'organizer' and user.organizer_id:
        extra['organizer_id'] = user.organizer_id

    # ── CREATE JWT TOKEN ─────────────────────────────────────────
    token_payload = {
        "user_id": user.user_id,
        "role"   : user.role,
        **extra
    }

    token = create_access_token(token_payload)

    return {
        'success' : True,
        'message' : 'Login successful',
        'token'   : token,
        'user_id' : user.user_id,
        'name'    : user.firstname + ' ' + user.lastname,
        'role'    : user.role,
        **extra
    }