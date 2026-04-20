from dataclasses import dataclass


@dataclass
class Warning:
    id: int
    player_id: int
    reason: str
    created_at: str
    officer_id: int