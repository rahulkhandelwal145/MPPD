#!/usr/bin/env python
"""Run Alembic migrations"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

os.chdir(project_root)

from alembic.config import Config
from alembic import command

# Setup Alembic config
cfg = Config(str(project_root / "backend" / "alembic.ini"))
cfg.set_main_option("sqlalchemy.url", "")  # We handle this in env.py

# Run upgrade
try:
    command.upgrade(cfg, "head")
    print("✓ Migration successful!")
except Exception as e:
    print(f"✗ Migration failed: {e}")
    sys.exit(1)
