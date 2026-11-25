from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_columns():
    """Ergänzt fehlende Spalten in bestehenden Tabellen und verbreitert Textfelder (einfache Migration ohne Alembic).
    Nur additive/verbreiternde Änderungen. Umbenennen/Löschen/Verkleinern bleibt manuell."""
    from sqlalchemy import inspect, text
    insp = inspect(engine)
    existing_tables = set(insp.get_table_names())
    with engine.begin() as conn:
        for table in Base.metadata.sorted_tables:
            if table.name not in existing_tables:
                continue
            cols = {c["name"]: c for c in insp.get_columns(table.name)}
            have = set(cols)
            for col in table.columns:
                if col.name in have:
                    # Textfelder nur verbreitern (nie verkleinern): VARCHAR(n) -> größer oder TEXT
                    old = cols[col.name]["type"]
                    old_len = getattr(old, "length", None)
                    new_len = getattr(col.type, "length", "n/a")
                    is_text = col.type.__class__.__name__ == "Text"
                    if old_len and ((is_text) or (isinstance(new_len, int) and new_len > old_len)):
                        ddl = col.type.compile(dialect=engine.dialect)
                        conn.execute(text(f'ALTER TABLE {table.name} ALTER COLUMN "{col.name}" TYPE {ddl}'))
                        print(f"DB: Spalte {table.name}.{col.name} verbreitert ({old_len} -> {ddl})")
                    continue
                ddl = col.type.compile(dialect=engine.dialect)
                conn.execute(text(f'ALTER TABLE {table.name} ADD COLUMN "{col.name}" {ddl}'))
                print(f"DB: Spalte {table.name}.{col.name} ergänzt")
                have.add(col.name)
            # REV03-01: Spalten mit festem Standardwert (z. B. Ja/Nein-Felder) dürfen in Altdaten nicht leer bleiben –
            # leere Werte machen sonst ganze Listen unlesbar (Fehler 500 in Pipeline/Anfragen nach dem Update auf v1.30).
            for col in table.columns:
                d = col.default
                if col.name not in have or col.primary_key or d is None or not getattr(d, "is_scalar", False):
                    continue
                if not isinstance(d.arg, bool):   # bewusst nur Ja/Nein-Felder: dort heißt leer nie „unbekannt“
                    continue
                res = conn.execute(text(f'UPDATE {table.name} SET "{col.name}" = :v WHERE "{col.name}" IS NULL'), {"v": d.arg})
                if res.rowcount:
                    print(f"DB: {res.rowcount} leere Werte in {table.name}.{col.name} mit Standard {d.arg!r} gefüllt")
