import sys
import os
from logging.config import fileConfig

from sqlalchemy import pool
from alembic import context

# Add backend app directory to path to resolve imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import DB config and models metadata
from app.database import Base, DATABASE_URL, engine
# Import models to ensure metadata is registered
from app.models.user import User
from app.models.applicant import Applicant
from app.models.application import Application
from app.models.document import Document
from app.models.ocr_result import OCRResult
from app.models.validation_report import ValidationReport
from app.models.policy_rule import PolicyRule
from app.models.scores import Scores
from app.models.recommendation import Recommendation
from app.models.fairness_check import FairnessCheck
from app.models.human_review import HumanReview
from app.models.audit_log import AuditLog

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    # Use the application's engine for connections
    connectable = engine

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata,
            render_as_batch=True  # Required for SQLite migration support
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
