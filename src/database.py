"""SQLite数据库表结构与初始化工具。后期可平滑迁移到MySQL。"""

from __future__ import annotations

import sqlite3
from pathlib import Path


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    anonymous_code TEXT UNIQUE NOT NULL,
    age_group TEXT,
    population_type TEXT,
    province TEXT,
    city TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS risk_assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    assessment_type TEXT NOT NULL,
    behavior_json TEXT NOT NULL,
    exposure_json TEXT,
    prep_json TEXT,
    risk_score REAL,
    risk_level TEXT,
    explanation TEXT,
    recommendation TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS screening_recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    risk_assessment_id INTEGER,
    exposure_hours INTEGER,
    symptoms TEXT,
    prep_status TEXT,
    pep_status TEXT,
    recommended_method TEXT,
    timing_advice TEXT,
    window_note TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(risk_assessment_id) REFERENCES risk_assessments(id)
);

CREATE TABLE IF NOT EXISTS terminal_devices (
    terminal_id TEXT PRIMARY KEY,
    site_name TEXT,
    province TEXT,
    city TEXT,
    status TEXT DEFAULT 'active',
    api_key_hash TEXT,
    last_seen_at TEXT
);

CREATE TABLE IF NOT EXISTS test_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    terminal_id TEXT,
    test_type TEXT NOT NULL,
    sample_type TEXT,
    c_line_score REAL,
    t_line_score REAL,
    result TEXT NOT NULL,
    image_path TEXT,
    raw_payload TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(terminal_id) REFERENCES terminal_devices(terminal_id)
);

CREATE TABLE IF NOT EXISTS interventions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    risk_assessment_id INTEGER,
    test_result_id INTEGER,
    risk_level TEXT,
    testing_advice TEXT,
    prep_advice TEXT,
    pep_advice TEXT,
    medication_reminder TEXT,
    pharmacy_guidance TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(risk_assessment_id) REFERENCES risk_assessments(id),
    FOREIGN KEY(test_result_id) REFERENCES test_results(id)
);

CREATE TABLE IF NOT EXISTS medical_sites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    site_type TEXT NOT NULL,
    province TEXT,
    city TEXT,
    district TEXT,
    address TEXT,
    phone TEXT,
    services TEXT,
    latitude REAL,
    longitude REAL,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS referrals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    medical_site_id INTEGER,
    referral_reason TEXT,
    urgency TEXT,
    status TEXT DEFAULT 'pending',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(medical_site_id) REFERENCES medical_sites(id)
);
"""


def connect(db_path: str | Path = "prep_guardian.db") -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: str | Path = "prep_guardian.db") -> None:
    with connect(db_path) as conn:
        conn.executescript(SCHEMA_SQL)
