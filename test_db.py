from sqlalchemy import create_engine, text

engine = create_engine("postgresql+psycopg://postgres:ClanOsiris_DiabloImmortal_2026!@localhost:5432/avertit_db")

with engine.connect() as conn:
    result = conn.execute(text("SELECT 1"))
    print("OK:", result.scalar())