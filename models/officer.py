from dataclasses import dataclass


@dataclass
class Officer:
    id: int
    ingame_name: str
    email: str
    password_hash: str
    is_active: bool = True