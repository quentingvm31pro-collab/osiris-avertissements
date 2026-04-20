from pydantic import BaseModel, EmailStr
from typing import List


class OfficerRegister(BaseModel):
    pseudo: str
    email: EmailStr
    password: str


class OfficerLogin(BaseModel):
    login: str
    password: str


class WarningCreate(BaseModel):
    pseudo: str
    reason: str
    date: str
    officer: str


class WarningUpdate(BaseModel):
    reason: str


class WarningOut(BaseModel):
    id: int
    reason: str
    date: str
    officer: str


class PlayerOut(BaseModel):
    player_id: int
    pseudo: str
    warnings: List[WarningOut]