from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from app.routers import auth
from app.routers import admin
from app.routers import organizer
from app.routers import participant
from app.routers import judge
from app.routers import public

app = FastAPI(
    title='Hackathon Management System'
)

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
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


# ── SWAGGER AUTHORIZE BUTTON ──────────────────────────────────────────────────
def custom_openapi():

    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version="1.0.0",
        routes=app.routes,
    )

    schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }

    for path in schema["paths"].values():
        for method in path.values():
            method["security"] = [{"BearerAuth": []}]

    app.openapi_schema = schema
    return schema


app.openapi = custom_openapi