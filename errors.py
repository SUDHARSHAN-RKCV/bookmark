# errors.py
from werkzeug.exceptions import HTTPException
import logging
from logging.handlers import RotatingFileHandler
import re
from flask import render_template, request, jsonify


class InvalidCredentialsError(Exception):
    """Raised when user login credentials are invalid."""
    pass


# ✅ Define a custom HTTPException subclass for 498
class CORSViolationError(HTTPException):
    code = 498
    description = "CORS policy violation"


def register_error_handlers(app):
    """Attach custom error handlers and logging to the Flask app."""

    # -----------------
    # Logging setup
    # -----------------
    if not app.debug:
        file_handler = RotatingFileHandler(
            'error_log.log',
            maxBytes=10_000_000,
            backupCount=5
        )
        file_handler.setLevel(logging.ERROR)
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s [%(module)s:%(lineno)d]'
        )
        file_handler.setFormatter(formatter)
        app.logger.addHandler(file_handler)

    def log_err(level, code, msg):
        app.logger.log(
            level,
            f"{code}: {msg} | Path={request.path} | IP={request.remote_addr} | Agent={request.user_agent}"
        )

    # -----------------
    # Basic SQL injection pattern check
    # -----------------
    @app.before_request
    def detect_sql_injection():
        suspicious_patterns = re.compile(r"(\bUNION\b|\bSELECT\b|\bDROP\b|\bINSERT\b|\bUPDATE\b|\bDELETE\b|--|;)", re.IGNORECASE)
        for param, value in {**request.args, **request.form}.items():
            if suspicious_patterns.search(value):
                log_err(logging.WARNING, "SQL-INJECTION", f"Param '{param}' with value '{value}'")
                return render_template('errors/400.html', error="Invalid request syntax"), 400

    # -----------------
    # Standard HTTP Errors
    # -----------------
    @app.errorhandler(400)
    def bad_request(error):
        log_err(logging.ERROR, 400, error)
        return render_template('errors/400.html', error=error), 400

    @app.errorhandler(401)
    def unauthorized(error):
        log_err(logging.ERROR, 401, error)
        return render_template('errors/401.html', error=error), 401

    @app.errorhandler(403)
    def forbidden(error):
        log_err(logging.ERROR, 403, error)
        return render_template('errors/403.html', error=error), 403

    @app.errorhandler(404)
    def page_not_found(error):
        log_err(logging.ERROR, 404, error)
        return render_template('errors/404.html', error=error), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        log_err(logging.ERROR, 405, error)
        return render_template('errors/405.html', error=error), 405

    @app.errorhandler(413)
    def payload_too_large(error):
        log_err(logging.ERROR, 413, error)
        return render_template('errors/413.html', error=error), 413

    @app.errorhandler(500)
    def internal_server_error(error):
        log_err(logging.ERROR, 500, error)
        return render_template('errors/500.html', error=error), 500

    # -----------------
    # ✅ Custom 498 CORS Error
    # -----------------
    @app.errorhandler(CORSViolationError)
    def cors_error(error):
        log_err(logging.WARNING, 498, f"CORS policy violation: {error}")
        return jsonify({"error": error.description}), 498

    # -----------------
    # Invalid credentials handler
    # -----------------
    @app.errorhandler(InvalidCredentialsError)
    def handle_invalid_login(error):
        log_err(logging.WARNING, "LOGIN", f"Invalid credentials attempt: {error}")
        return render_template('errors/401.html', error="Invalid username or password"), 401

    # -----------------
    # Catch-all exception
    # -----------------
    @app.errorhandler(Exception)
    def handle_unexpected_exception(error):
        log_err(logging.ERROR, "EXCEPTION", error)
        return render_template('errors/500.html', error=error), 500
