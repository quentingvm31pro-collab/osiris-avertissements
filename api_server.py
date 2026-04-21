from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel

from database import Base, engine, get_db
from models import Officer, Player, Warning
from auth import (
    hash_password,
    verify_password,
    create_access_token,
    verify_access_token,
)


class OfficerRegister(BaseModel):
    pseudo: str
    email: str
    password: str


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
         "http://localhost:5173",
         "http://127.0.0.1:5500",
         "http://localhost:5500",
         "https://osiris-avertissements-i2r8l5asy.vercel.app",
         "https://osiris-avertissements-web.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.options("/{rest_of_path:path}")
def preflight_handler(rest_of_path: str):
    return Response(status_code=200)


Base.metadata.create_all(bind=engine)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/officers/login")


def get_current_officer(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    print("TOKEN RECU =", token, flush=True)

    payload = verify_access_token(token)
    print("PAYLOAD =", payload, flush=True)

    officer_id = payload.get("officer_id")

    if not officer_id:
        raise HTTPException(status_code=401, detail="Invalid token: officer_id missing")

    officer = db.query(Officer).filter(Officer.id == officer_id).first()
    if not officer:
        raise HTTPException(status_code=401, detail="Officer not found")

    return officer


@app.get("/")
def root():
    return {"status": "Server running"}


@app.post("/players")
def create_player(
    name: str,
    db: Session = Depends(get_db),
    current_officer: Officer = Depends(get_current_officer)
):
    existing_player = db.query(Player).filter(Player.pseudo == name).first()
    if existing_player:
        return {
            "id": existing_player.id,
            "pseudo": existing_player.pseudo
        }

    new_player = Player(pseudo=name)
    db.add(new_player)
    db.commit()
    db.refresh(new_player)

    return {
        "id": new_player.id,
        "pseudo": new_player.pseudo
    }


@app.get("/players")
def get_players(
    db: Session = Depends(get_db),
    current_officer: Officer = Depends(get_current_officer)
):
    players = db.query(Player).all()
    return [
        {
            "id": player.id,
            "pseudo": player.pseudo
        }
        for player in players
    ]


@app.get("/players-with-warnings")
def get_players_with_warnings(
    db: Session = Depends(get_db),
    current_officer: Officer = Depends(get_current_officer)
):
    players = db.query(Player).all()
    warnings = db.query(Warning).all()

    warnings_by_player_id = {}
    for warning in warnings:
        warnings_by_player_id.setdefault(warning.player_id, []).append({
            "id": warning.id,
            "reason": warning.reason,
            "date": warning.date,
            "officer": warning.officer,
        })

    return [
        {
            "id": player.id,
            "pseudo": player.pseudo,
            "warnings": warnings_by_player_id.get(player.id, []),
        }
        for player in players
    ]


@app.post("/warnings")
def create_warning(
    player_id: int,
    reason: str,
    date: str,
    db: Session = Depends(get_db),
    current_officer: Officer = Depends(get_current_officer)
):
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    new_warning = Warning(
        player_id=player_id,
        reason=reason,
        date=date,
        officer=current_officer.pseudo
    )

    db.add(new_warning)
    db.commit()
    db.refresh(new_warning)

    return {
        "id": new_warning.id,
        "player_id": new_warning.player_id,
        "reason": new_warning.reason,
        "date": new_warning.date,
        "officer": new_warning.officer
    }


@app.get("/warnings")
def get_warnings(
    db: Session = Depends(get_db),
    current_officer: Officer = Depends(get_current_officer)
):
    warnings = db.query(Warning).all()
    return [
        {
            "id": warning.id,
            "player_id": warning.player_id,
            "reason": warning.reason,
            "date": warning.date,
            "officer": warning.officer
        }
        for warning in warnings
    ]


@app.post("/officers/register")
def register_officer(
    data: OfficerRegister,
    db: Session = Depends(get_db)
):
    pseudo = data.pseudo
    email = data.email
    password = data.password

    existing_officer = db.query(Officer).filter(
        (Officer.pseudo == pseudo) | (Officer.email == email)
    ).first()

    if existing_officer:
        raise HTTPException(status_code=400, detail="Officer already exists")

    if len(password.encode("utf-8")) > 72:
        raise HTTPException(
            status_code=400,
            detail="Password too long. Maximum 72 bytes for bcrypt."
        )

    new_officer = Officer(
        pseudo=pseudo,
        email=email,
        password_hash=hash_password(password)
    )

    db.add(new_officer)
    db.commit()
    db.refresh(new_officer)

    return {
        "id": new_officer.id,
        "pseudo": new_officer.pseudo,
        "email": new_officer.email
    }


@app.post("/officers/login")
def login_officer(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    officer = db.query(Officer).filter(Officer.email == form_data.username).first()

    if not officer or not verify_password(form_data.password, officer.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token({"officer_id": officer.id})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "officer": {
            "id": officer.id,
            "pseudo": officer.pseudo,
            "email": officer.email
        }
    }


@app.get("/players/{player_id}/warnings")
def get_player_warnings(
    player_id: int,
    db: Session = Depends(get_db),
    current_officer: Officer = Depends(get_current_officer)
):
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    warnings = db.query(Warning).filter(Warning.player_id == player_id).all()

    return [
        {
            "id": warning.id,
            "reason": warning.reason,
            "date": warning.date,
            "officer": warning.officer
        }
        for warning in warnings
    ]


@app.put("/warnings/{warning_id}")
def update_warning(
    warning_id: int,
    reason: str,
    date: str,
    db: Session = Depends(get_db),
    current_officer: Officer = Depends(get_current_officer)
):
    warning = db.query(Warning).filter(Warning.id == warning_id).first()

    if not warning:
        raise HTTPException(status_code=404, detail="Warning not found")

    warning.reason = reason
    warning.date = date
    warning.officer = current_officer.pseudo

    db.commit()
    db.refresh(warning)

    return {
        "id": warning.id,
        "player_id": warning.player_id,
        "reason": warning.reason,
        "date": warning.date,
        "officer": warning.officer
    }


@app.delete("/warnings/{warning_id}")
def delete_warning(
    warning_id: int,
    db: Session = Depends(get_db),
    current_officer: Officer = Depends(get_current_officer)
):
    warning = db.query(Warning).filter(Warning.id == warning_id).first()

    if not warning:
        raise HTTPException(status_code=404, detail="Warning not found")

    db.delete(warning)
    db.commit()

    return {"message": "Warning deleted"}


@app.delete("/players/{player_id}")
def delete_player(
    player_id: int,
    db: Session = Depends(get_db),
    current_officer: Officer = Depends(get_current_officer)
):
    player = db.query(Player).filter(Player.id == player_id).first()

    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    db.delete(player)
    db.commit()

    return {"message": "Player deleted"}


@app.delete("/officers/{officer_id}")
def delete_officer(
    officer_id: int,
    db: Session = Depends(get_db),
    current_officer: Officer = Depends(get_current_officer)
):
    officer = db.query(Officer).filter(Officer.id == officer_id).first()

    if not officer:
        raise HTTPException(status_code=404, detail="Officer not found")

    if officer.id == current_officer.id:
        raise HTTPException(status_code=400, detail="You cannot delete your own account")

    db.delete(officer)
    db.commit()

    return {"message": "Officer deleted"}