

from fastapi import FastAPI

from app.routers import auth
from app.routers import admin
from app.routers import organizer
from app.routers import participant
from app.routers import judge
from app.routers import public

app = FastAPI(
    title='Hackathon Management System'
)

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(organizer.router)
app.include_router(participant.router)
app.include_router(judge.router)
app.include_router(public.router)


@app.get('/')
def home():

    return {
        'message': 'Hackathon Management System API Running'
    }