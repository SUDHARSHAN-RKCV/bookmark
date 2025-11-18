#security.py
from flask import request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = None

def register_security_features(app):
    """Attach Flask-Limiter safely to routes."""
    global limiter
    limiter = Limiter(
        key_func=get_remote_address,
        app=app,
        default_limits=["200 per day", "50 per hour"],
        storage_uri="memory://"
    )

    # Rate-limit home
    if 'home' in app.view_functions:
        limiter.limit("30 per minute")(app.view_functions['home'])

    # Rate-limit team_page
    if 'team_page' in app.view_functions:
        limiter.limit("30 per minute")(app.view_functions['team_page'])

    # Rate-limit login with username/IP key
    if 'login' in app.view_functions:
        limiter.limit("5 per 15 minutes", key_func=_login_key)(app.view_functions['login'])

    # 429 logging
    _setup_rate_limit_logging(app)

def _login_key():
    return request.form.get('username') or get_remote_address()

def _setup_rate_limit_logging(app):
    @app.errorhandler(429)
    def too_many_requests(error):
        limit_info = getattr(error, "description", "Rate limit exceeded")
        app.logger.warning(
            f"429 Too Many Requests: {limit_info}\n"
            f"Path: {request.path}\n"
            f"Client IP: {request.remote_addr}\n"
            f"User Agent: {request.user_agent}\n"
        )
        return (
            app.jinja_env.get_template('errors/429.html').render(error=error),
            429
        )
