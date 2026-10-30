"""Shared PostgreSQL models for FacultyLink (web + mobile)."""

from __future__ import annotations

from datetime import date, datetime, timezone
from uuid import uuid4

from sqlalchemy import CheckConstraint, JSON, Index, UniqueConstraint
from sqlalchemy.orm import validates
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_public_id(prefix: str = "") -> str:
    token = uuid4().hex[:12]
    return f"{prefix}{token}" if prefix else token


class TimestampMixin:
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )


class User(TimestampMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(40), unique=True, nullable=False, default=lambda: new_public_id("usr_"))
    email = db.Column(db.String(180), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, index=True)  # administrator | reviewer | faculty
    full_name = db.Column(db.String(160), nullable=False)
    office = db.Column(db.String(200))
    contact = db.Column(db.String(80))
    specialization = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    must_change_password = db.Column(db.Boolean, nullable=False, default=False)
    auth_epoch = db.Column(db.Integer, nullable=False, default=0)

    faculty_profile = db.relationship(
        "FacultyProfile",
        back_populates="user",
        uselist=False,
        foreign_keys="FacultyProfile.user_id",
    )
    notifications = db.relationship("Notification", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_session_user(self) -> dict:
        return {
            "id": self.public_id,
            "email": self.email,
            "role": self.role,
            "name": self.full_name,
            "office": self.office or "",
            "contact": self.contact or "",
            "specialization": self.specialization or "",
            "mustChangePassword": self.must_change_password,
        }


class FacultyProfile(TimestampMixin, db.Model):
    __tablename__ = "faculty_profiles"

    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(40), unique=True, nullable=False, default=lambda: new_public_id("fac_"))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    employee_no = db.Column(db.String(40), unique=True, nullable=False)
    current_rank = db.Column(db.String(80), nullable=False)
    target_rank = db.Column(db.String(80))
    department = db.Column(db.String(160), nullable=False)
    college = db.Column(db.String(160), nullable=False)
    campus = db.Column(db.String(80), nullable=False, default="Main Campus")
    years_of_service = db.Column(db.Integer, nullable=False, default=0)
    employment_status = db.Column(db.String(40), nullable=False, default="Active")
    reviewer_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), index=True)
    evaluation_eligibility_json = db.Column(JSON, nullable=True)

    user = db.relationship("User", back_populates="faculty_profile", foreign_keys=[user_id])
    reviewer = db.relationship("User", foreign_keys=[reviewer_user_id])
    documents = db.relationship("Document", back_populates="faculty_profile", cascade="all, delete-orphan")
    kra_scores = db.relationship("KraScore", back_populates="faculty_profile", cascade="all, delete-orphan")
    rank_simulation = db.relationship(
        "RankSimulation", back_populates="faculty_profile", uselist=False, cascade="all, delete-orphan"
    )

    def to_web_faculty(self) -> dict:
        return {
            "id": self.public_id,
            "userId": self.user.public_id,
            "name": self.user.full_name,
            "email": self.user.email,
            "employeeNo": self.employee_no,
            "rank": self.current_rank,
            "department": self.department,
            "college": self.college,
            "campus": self.campus,
            "status": self.employment_status,
            "reviewerId": self.reviewer.public_id if self.reviewer else None,
            "yearsOfService": self.years_of_service,
            "targetRank": self.target_rank or "",
        }


class Document(TimestampMixin, db.Model):
    __tablename__ = "documents"

    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(40), unique=True, nullable=False, default=lambda: new_public_id("doc_"))
    faculty_profile_id = db.Column(db.Integer, db.ForeignKey("faculty_profiles.id"), nullable=False, index=True)
    reviewer_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), index=True)
    title = db.Column(db.String(255), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500))
    mime_type = db.Column(db.String(120))
    file_size = db.Column(db.Integer)
    file_hash = db.Column(db.String(64))
    kra_id = db.Column(db.String(40), index=True)
    criterion_id = db.Column(db.String(80))
    indicator_id = db.Column(db.String(80))
    status = db.Column(db.String(40), nullable=False, default="pending_review", index=True)
    extracted_info = db.Column(JSON, nullable=False, default=dict)
    extracted_text = db.Column(db.Text)
    ocr_confidence = db.Column(db.Float)
    ocr_status = db.Column(db.String(40), default="pending")
    validation_result = db.Column(db.Text)
    reviewer_remarks = db.Column(db.Text)
    reviewer_score = db.Column(db.Float)
    estimated_points = db.Column(db.Float, default=0)
    verified_points = db.Column(db.Float, default=0)
    submitted_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    reviewed_at = db.Column(db.DateTime(timezone=True))
    deleted_at = db.Column(db.DateTime(timezone=True))
    version_number = db.Column(db.Integer, nullable=False, default=1)
    replaces_document_id = db.Column(db.Integer, db.ForeignKey("documents.id"), index=True)

    faculty_profile = db.relationship("FacultyProfile", back_populates="documents")
    replaces_document = db.relationship("Document", remote_side=[id], foreign_keys=[replaces_document_id])
    reviewer = db.relationship("User", foreign_keys=[reviewer_user_id])
    teaching_evaluations = db.relationship(
        "DocumentTeachingEvaluation",
        back_populates="document",
        cascade="all, delete-orphan",
        lazy="dynamic",
        order_by="DocumentTeachingEvaluation.academic_year, DocumentTeachingEvaluation.semester",
    )


class DocumentTeachingEvaluation(TimestampMixin, db.Model):
    """One SET or SEF semester evaluation linked to an uploaded document (Phase 1 storage only)."""

    __tablename__ = "document_teaching_evaluations"

    EVALUATION_TYPE_SET = "SET"
    EVALUATION_TYPE_SEF = "SEF"
    INDICATOR_BY_TYPE = {
        EVALUATION_TYPE_SET: "kra1-a-student",
        EVALUATION_TYPE_SEF: "kra1-a-supervisor",
    }

    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(
        db.String(40), unique=True, nullable=False, default=lambda: new_public_id("tev_")
    )
    document_id = db.Column(
        db.Integer, db.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    evaluation_type = db.Column(db.String(8), nullable=False, index=True)
    indicator_id = db.Column(db.String(80), nullable=False, index=True)
    academic_year = db.Column(db.String(20), nullable=True)
    semester = db.Column(db.String(40), nullable=True)
    rating_raw = db.Column(db.String(120), nullable=True)
    rating_scale = db.Column(db.Float, nullable=True)
    rating_percent = db.Column(db.Float, nullable=True)
    extracted_metadata = db.Column(JSON, nullable=False, default=dict)
    ocr_verification_status = db.Column(db.String(40), nullable=True)
    reviewer_validation_status = db.Column(db.String(40), nullable=True)
    reviewer_remarks = db.Column(db.Text, nullable=True)
    correction_history_json = db.Column(JSON, nullable=False, default=list)
    extraction_source = db.Column(db.String(40), nullable=False, default="ocr")
    source_section_ref = db.Column(db.String(120), nullable=True)

    document = db.relationship("Document", back_populates="teaching_evaluations")

    __table_args__ = (
        CheckConstraint(
            "evaluation_type IN ('SET', 'SEF')",
            name="ck_document_teaching_evaluations_type",
        ),
        CheckConstraint(
            "(evaluation_type = 'SET' AND indicator_id = 'kra1-a-student') OR "
            "(evaluation_type = 'SEF' AND indicator_id = 'kra1-a-supervisor')",
            name="ck_document_teaching_evaluations_indicator",
        ),
        Index(
            "uq_document_teaching_eval_period",
            "document_id",
            "evaluation_type",
            "academic_year",
            "semester",
            unique=True,
            postgresql_where=db.text("academic_year IS NOT NULL AND semester IS NOT NULL"),
            sqlite_where=db.text("academic_year IS NOT NULL AND semester IS NOT NULL"),
        ),
    )

    @validates("evaluation_type", "indicator_id")
    def _validate_type_indicator_pair(self, key: str, value: str) -> str:
        if key == "evaluation_type":
            et = (value or "").strip().upper()
            if et not in (self.EVALUATION_TYPE_SET, self.EVALUATION_TYPE_SEF):
                raise ValueError("evaluation_type must be SET or SEF")
            expected = self.INDICATOR_BY_TYPE[et]
            if self.indicator_id and self.indicator_id != expected:
                raise ValueError(f"indicator_id must be {expected} for evaluation type {et}")
            if not self.indicator_id:
                self.indicator_id = expected
            return et
        ind = (value or "").strip()
        et = (self.evaluation_type or "").strip().upper()
        if et:
            expected = self.INDICATOR_BY_TYPE.get(et)
            if expected and ind != expected:
                raise ValueError(f"indicator_id must be {expected} for evaluation type {et}")
        return ind

    @property
    def faculty_profile_id(self) -> int | None:
        return self.document.faculty_profile_id if self.document else None


class DocumentOcrJob(TimestampMixin, db.Model):
    """Persistent OCR work queue (recoverable across worker restarts)."""

    __tablename__ = "document_ocr_jobs"

    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey("documents.id"), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default="pending", index=True)
    attempts = db.Column(db.Integer, nullable=False, default=0)
    max_attempts = db.Column(db.Integer, nullable=False, default=3)
    file_hash = db.Column(db.String(64), nullable=False)
    locked_at = db.Column(db.DateTime(timezone=True))
    locked_by = db.Column(db.String(64))
    last_error = db.Column(db.Text)

    document = db.relationship("Document", backref=db.backref("ocr_jobs", lazy="dynamic"))


class KraScoringRule(TimestampMixin, db.Model):
    __tablename__ = "kra_scoring_rules"

    id = db.Column(db.Integer, primary_key=True)
    kra_key = db.Column(db.String(40), unique=True, nullable=False)
    label = db.Column(db.String(120), nullable=False)
    base_points = db.Column(db.Float)
    max_points = db.Column(db.Float)
    keywords = db.Column(JSON, default=list)
    config_json = db.Column(JSON, default=dict)
    is_active = db.Column(db.Boolean, nullable=False, default=True)


class KraConfiguration(TimestampMixin, db.Model):
    __tablename__ = "kra_configuration"

    id = db.Column(db.Integer, primary_key=True)
    guideline_label = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(40), nullable=False, default="draft")
    published_at = db.Column(db.DateTime(timezone=True))
    rank_weights = db.Column(JSON, nullable=False, default=dict)
    settings_json = db.Column(JSON, nullable=False, default=dict)


class KraScore(TimestampMixin, db.Model):
    __tablename__ = "kra_scores"
    __table_args__ = (UniqueConstraint("faculty_profile_id", "kra_key", name="uq_kra_score_faculty_kra"),)

    id = db.Column(db.Integer, primary_key=True)
    faculty_profile_id = db.Column(db.Integer, db.ForeignKey("faculty_profiles.id"), nullable=False)
    kra_key = db.Column(db.String(40), nullable=False)
    estimated_points = db.Column(db.Float, nullable=False, default=0)
    verified_points = db.Column(db.Float, nullable=False, default=0)
    target_points = db.Column(db.Float)
    document_count = db.Column(db.Integer, nullable=False, default=0)
    status_label = db.Column(db.String(80), default="In progress")
    breakdown_json = db.Column(JSON, default=list)

    faculty_profile = db.relationship("FacultyProfile", back_populates="kra_scores")


class RankSimulation(TimestampMixin, db.Model):
    __tablename__ = "rank_simulations"

    id = db.Column(db.Integer, primary_key=True)
    faculty_profile_id = db.Column(db.Integer, db.ForeignKey("faculty_profiles.id"), unique=True, nullable=False)
    current_rank = db.Column(db.String(80), nullable=False)
    target_rank = db.Column(db.String(80), nullable=False)
    estimated_total_points = db.Column(db.Float, nullable=False, default=0)
    verified_total_points = db.Column(db.Float, nullable=False, default=0)
    readiness_label = db.Column(db.String(120))
    missing_requirements = db.Column(db.Text)
    snapshot_json = db.Column(JSON, default=dict)
    simulated_at = db.Column(db.DateTime(timezone=True), default=utcnow)

    faculty_profile = db.relationship("FacultyProfile", back_populates="rank_simulation")


class EvaluationPeriod(TimestampMixin, db.Model):
    __tablename__ = "evaluation_periods"

    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(40), unique=True, nullable=False, default=lambda: new_public_id("per_"))
    period_type = db.Column(db.String(40), nullable=False)
    label = db.Column(db.String(200), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    submission_open = db.Column(db.Date)
    submission_close = db.Column(db.Date)
    review_open = db.Column(db.Date)
    review_close = db.Column(db.Date)
    status = db.Column(db.String(40), nullable=False, default="draft")
    timezone = db.Column(db.String(64), default="Asia/Manila")


class Notification(TimestampMixin, db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(40), unique=True, nullable=False, default=lambda: new_public_id("ntf_"))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    read = db.Column(db.Boolean, nullable=False, default=False)
    kind = db.Column(db.String(60))
    related_document_id = db.Column(db.String(40))
    related_faculty_id = db.Column(db.String(40))

    user = db.relationship("User", back_populates="notifications")


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(40), unique=True, nullable=False, default=lambda: new_public_id("aud_"))
    actor_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), index=True)
    action = db.Column(db.String(200), nullable=False)
    target_id = db.Column(db.String(80))
    detail = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

    actor = db.relationship("User", foreign_keys=[actor_user_id])
