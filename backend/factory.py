from flask import Flask, jsonify
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from auth import auth_bp
from auth.admin_routes import admin_bp
from documents.routes import admin_docs_bp, faculty_docs_bp, reviewer_docs_bp
from faculty_routes import faculty_bp
from reviewer_routes import reviewer_bp
from kra_configuration.routes import kra_config_admin_bp
from auth_models import RevokedToken
from cli import (
    create_administrator,
    documents_list_legacy_drafts,
    documents_promote_legacy_drafts,
    documents_purge_set_sef,
    documents_reassess_set_sef_simulation,
    documents_refresh_set_sef_extraction,
    ocr_enqueue_stale,
    ocr_worker,
)
from config import Config
from extensions import cors, db, jwt, migrate


def create_app(config_class: type = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.config["SQLALCHEMY_DATABASE_URI"] = config_class.sqlalchemy_database_uri()
    app.config["UPLOAD_FOLDER"].mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(
        app,
        resources={
            r"/api/*": {
                "origins": config_class.cors_origins(),
                "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization", "Accept"],
            }
        },
        supports_credentials=True,
    )

    import models  # noqa: F401 — register models with SQLAlchemy metadata
    import auth_models  # noqa: F401

    register_jwt_handlers(app)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(kra_config_admin_bp, url_prefix="/api/admin")
    app.register_blueprint(faculty_bp)
    app.register_blueprint(reviewer_bp)
    app.register_blueprint(faculty_docs_bp)
    app.register_blueprint(reviewer_docs_bp)
    app.register_blueprint(admin_docs_bp)
    app.cli.add_command(create_administrator)
    app.cli.add_command(ocr_worker)
    app.cli.add_command(ocr_enqueue_stale)
    app.cli.add_command(documents_list_legacy_drafts)
    app.cli.add_command(documents_promote_legacy_drafts)
    app.cli.add_command(documents_refresh_set_sef_extraction)
    app.cli.add_command(documents_purge_set_sef)
    app.cli.add_command(documents_reassess_set_sef_simulation)

    register_routes(app)

    from documents.ocr.config import refresh_tesseract_availability

    with app.app_context():
        status = refresh_tesseract_availability()
        if not status.available:
            app.logger.warning("OCR unavailable: %s", status.message)
        else:
            app.logger.info("OCR ready (Tesseract %s)", status.tesseract_version)

    return app


def register_jwt_handlers(app: Flask) -> None:
    from models import User

    @jwt.token_in_blocklist_loader
    def _token_in_blocklist(_jwt_header, jwt_payload):
        jti = jwt_payload.get("jti")
        if not jti:
            return False
        return db.session.query(RevokedToken.id).filter_by(jti=jti).first() is not None

    @jwt.token_verification_loader
    def _verify_epoch(_jwt_header, jwt_payload):
        public_id = jwt_payload.get("sub")
        if not public_id:
            return False
        user = User.query.filter_by(public_id=public_id).first()
        if not user or not user.is_active:
            return False
        token_epoch = jwt_payload.get("epoch")
        if token_epoch is None:
            return True
        if token_epoch != user.auth_epoch:
            return False
        claim_must_change = jwt_payload.get("mustChangePassword")
        if claim_must_change is not None and claim_must_change != user.must_change_password:
            return False
        return True


def register_routes(app: Flask) -> None:
    @app.get("/api/health")
    def health():
        payload = {
            "status": "ok",
            "application": "FacultyLink API",
            "message": "Backend is running",
            "guideline": Config.GUIDELINE_LABEL,
            "database": "unknown",
        }
        try:
            db.session.execute(text("SELECT 1"))
            payload["database"] = "connected"
        except SQLAlchemyError as error:
            payload["database"] = "error"
            payload["databaseMessage"] = "Could not reach PostgreSQL. Check DATABASE_URL and that the server is running."
            app.logger.warning("Database health check failed: %s", error)
        from documents.ocr.config import ocr_runtime_status

        ocr = ocr_runtime_status()
        payload["ocr"] = {
            "available": ocr.available,
            "message": ocr.message,
            "tesseractVersion": ocr.tesseract_version,
        }
        return jsonify(payload)

    @app.get("/")
    def root():
        return jsonify(
            {
                "name": "FacultyLink API",
                "health": "/api/health",
                "phase": "Phase 3 authentication live under /api/auth. Domain APIs follow in Phase 4+.",
            }
        )
