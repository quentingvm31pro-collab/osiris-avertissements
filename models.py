from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship

from database import Base


class Officer(Base):
    __tablename__ = "officers"

    id = Column(Integer, primary_key=True, index=True)
    pseudo = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    pseudo = Column(String, unique=True, nullable=False)

    warnings = relationship("Warning", back_populates="player", cascade="all, delete")


class Warning(Base):
    __tablename__ = "warnings"

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    reason = Column(Text, nullable=False)
    date = Column(String, nullable=False)
    officer = Column(String, nullable=False)

    player = relationship("Player", back_populates="warnings")