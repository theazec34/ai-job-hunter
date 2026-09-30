import os
import sqlite3
import subprocess
import sys
from pathlib import Path


def test_alembic_adopts_phase_one_database_without_losing_data(tmp_path: Path):
    database_path = tmp_path / "legacy.db"
    with sqlite3.connect(database_path) as connection:
        connection.executescript(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                email VARCHAR(320) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                created_at DATETIME NOT NULL
            );
            CREATE INDEX ix_users_email ON users (email);
            CREATE TABLE profiles (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL UNIQUE REFERENCES users(id),
                name VARCHAR(120) NOT NULL,
                headline VARCHAR(180) NOT NULL,
                skills JSON NOT NULL,
                desired_roles JSON NOT NULL,
                preferred_countries JSON NOT NULL
            );
            CREATE INDEX ix_profiles_user_id ON profiles (user_id);
            CREATE TABLE jobs (
                id INTEGER PRIMARY KEY,
                source VARCHAR(50) NOT NULL,
                external_id VARCHAR(160) NOT NULL,
                title VARCHAR(180) NOT NULL,
                company VARCHAR(180) NOT NULL,
                country VARCHAR(100) NOT NULL,
                location VARCHAR(180) NOT NULL,
                description TEXT NOT NULL,
                url VARCHAR(2048) NOT NULL,
                employment_type VARCHAR(80) NOT NULL,
                created_at DATETIME NOT NULL,
                CONSTRAINT uq_job_source_external UNIQUE (source, external_id)
            );
            INSERT INTO users VALUES (
                1,
                'legacy@example.com',
                'hash',
                '2026-01-01 00:00:00'
            );
            """
        )

    environment = os.environ | {
        "DATABASE_URL": f"sqlite+pysqlite:///{database_path}",
        "JWT_SECRET": "migration-test-secret-at-least-thirty-two-characters",
    }
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=Path(__file__).parents[1],
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )

    with sqlite3.connect(database_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        job_columns = {row[1] for row in connection.execute("PRAGMA table_info(jobs)")}
        legacy_email = connection.execute("SELECT email FROM users WHERE id = 1").fetchone()
        revision = connection.execute("SELECT version_num FROM alembic_version").fetchone()

    assert {"users", "profiles", "jobs", "resume_profiles", "applications"} <= tables
    assert {
        "salary_min",
        "salary_max",
        "salary_currency",
        "workplace_mode",
        "legitimacy_status",
        "legitimacy_reasons",
    } <= job_columns
    assert legacy_email == ("legacy@example.com",)
    assert revision == ("d3bc58a00d0d",)
