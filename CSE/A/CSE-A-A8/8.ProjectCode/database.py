"""
database.py
-----------
SQLite database engine, session factory, and CRUD helper functions
built on SQLAlchemy for the Medical Lab AI platform.

All Streamlit pages should go through the helper functions in this
module rather than opening raw sessions, so that error handling and
commit/rollback behaviour stays consistent everywhere.
"""

import os
from contextlib import contextmanager
from datetime import datetime

from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker

from models import Base, Report, TestResult, HealthInsight

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)

DB_PATH = os.path.join(DATA_DIR, "medical_lab.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

# check_same_thread=False is required because Streamlit can access the
# connection from different internal threads during a single session.
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db():
    """Create all tables if they do not already exist. Safe to call every run."""
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_session():
    """Context manager yielding a SQLAlchemy session with commit/rollback handling."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Report CRUD
# ---------------------------------------------------------------------------

def create_report(file_name: str, file_type: str) -> int:
    """Insert a new report row with status 'Pending' and return its id."""
    with get_session() as session:
        report = Report(
            file_name=file_name,
            file_type=file_type,
            processing_status="Pending",
            upload_date=datetime.utcnow(),
        )
        session.add(report)
        session.flush()
        return report.id


def update_report_status(report_id: int, status: str, error_message: str = None,
                          raw_text: str = None):
    with get_session() as session:
        report = session.query(Report).filter(Report.id == report_id).first()
        if report is None:
            return
        report.processing_status = status
        if error_message is not None:
            report.error_message = error_message
        if raw_text is not None:
            report.raw_text = raw_text


def get_all_reports():
    with get_session() as session:
        reports = (
            session.query(Report).order_by(desc(Report.upload_date)).all()
        )
        session.expunge_all()
        return reports


def get_report_by_id(report_id: int):
    with get_session() as session:
        report = session.query(Report).filter(Report.id == report_id).first()
        if report:
            # Touch relationship so it loads before session closes
            _ = list(report.test_results)
            session.expunge_all()
        return report


def delete_report(report_id: int):
    with get_session() as session:
        report = session.query(Report).filter(Report.id == report_id).first()
        if report:
            session.delete(report)


# ---------------------------------------------------------------------------
# TestResult CRUD
# ---------------------------------------------------------------------------

def save_test_results(report_id: int, results: list) -> list:
    """
    Save a list of extracted+classified test result dicts to the DB.

    Each dict is expected to have keys:
        test_name, result_value, unit, reference_low, reference_high,
        status, test_date, confidence_score
    Returns the list of newly created TestResult ids.
    """
    new_ids = []
    with get_session() as session:
        for r in results:
            tr = TestResult(
                report_id=report_id,
                test_name=r.get("test_name"),
                result_value=r.get("result_value"),
                unit=r.get("unit"),
                reference_low=r.get("reference_low"),
                reference_high=r.get("reference_high"),
                status=r.get("status"),
                test_date=r.get("test_date"),
                confidence_score=r.get("confidence_score", 0.0),
            )
            session.add(tr)
            session.flush()
            new_ids.append(tr.id)
    return new_ids


def get_results_for_report(report_id: int):
    with get_session() as session:
        results = (
            session.query(TestResult)
            .filter(TestResult.report_id == report_id)
            .all()
        )
        session.expunge_all()
        return results


def get_all_test_results():
    with get_session() as session:
        results = session.query(TestResult).all()
        session.expunge_all()
        return results


def get_results_by_test_name(test_name: str):
    """Used for building a trend line across all reports for one test."""
    with get_session() as session:
        results = (
            session.query(TestResult, Report)
            .join(Report, TestResult.report_id == Report.id)
            .filter(TestResult.test_name == test_name)
            .order_by(Report.upload_date.asc())
            .all()
        )
        session.expunge_all()
        return results


def get_distinct_test_names():
    with get_session() as session:
        names = (
            session.query(TestResult.test_name)
            .distinct()
            .order_by(TestResult.test_name.asc())
            .all()
        )
        return [n[0] for n in names]


# ---------------------------------------------------------------------------
# HealthInsight CRUD
# ---------------------------------------------------------------------------

def save_health_insight(test_result_id: int, explanation: str,
                         possible_causes: str, recommendations: str) -> int:
    with get_session() as session:
        insight = HealthInsight(
            test_result_id=test_result_id,
            explanation=explanation,
            possible_causes=possible_causes,
            recommendations=recommendations,
            created_at=datetime.utcnow(),
        )
        session.add(insight)
        session.flush()
        return insight.id


def get_insight_for_test_result(test_result_id: int):
    with get_session() as session:
        insight = (
            session.query(HealthInsight)
            .filter(HealthInsight.test_result_id == test_result_id)
            .order_by(desc(HealthInsight.created_at))
            .first()
        )
        session.expunge_all()
        return insight


# ---------------------------------------------------------------------------
# Dashboard aggregate stats
# ---------------------------------------------------------------------------

def get_dashboard_stats():
    with get_session() as session:
        total_reports = session.query(Report).count()
        total_tests = session.query(TestResult).count()
        normal = session.query(TestResult).filter(TestResult.status == "NORMAL").count()
        abnormal = (
            session.query(TestResult)
            .filter(TestResult.status.in_(["LOW", "HIGH"]))
            .count()
        )
        # "Critical" heuristic: result deviates by more than 50% from the
        # nearest breached reference boundary.
        critical = 0
        for tr in session.query(TestResult).filter(TestResult.status.in_(["LOW", "HIGH"])):
            if tr.result_value is None:
                continue
            if tr.status == "LOW" and tr.reference_low:
                if tr.reference_low > 0 and tr.result_value < tr.reference_low * 0.5:
                    critical += 1
            elif tr.status == "HIGH" and tr.reference_high:
                if tr.result_value > tr.reference_high * 1.5:
                    critical += 1
        return {
            "total_reports": total_reports,
            "total_tests": total_tests,
            "normal": normal,
            "abnormal": abnormal,
            "critical": critical,
        }
