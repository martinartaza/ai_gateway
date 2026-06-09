#!/usr/bin/env python3
"""Create all tables. Run once before first startup: python init_db.py"""
from app.database import Base, engine
from app import models  # noqa: F401 — registers models with Base metadata

Base.metadata.create_all(bind=engine)
print("Tables created.")
