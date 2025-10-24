"""
Flask Application Factory for Loan Dashboard

A personal loan monitoring tool built with Flask for tracking multiple loans,
calculating interest, managing repayment schedules, and providing prepayment forecasting.
"""
from flask import Flask, render_template, session
from flask_session import Session
import os

def create_app(config=None):
    """
    Create and configure Flask application.

    Args:
        config: Optional configuration dictionary

    Returns:
        Configured Flask application instance
    """
    app = Flask(__name__)

    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24))
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_PERMANENT'] = False
    app.config['SESSION_FILE_DIR'] = './flask_session'
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS

    # Apply custom config if provided
    if config:
        app.config.update(config)

    # Initialize extensions
    Session(app)

    # Register blueprints
    from blueprints.dashboard import dashboard_bp
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')

    # Root route
    @app.route('/')
    def index():
        """Home page route."""
        return render_template('index.html')

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors."""
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        return render_template('errors/500.html'), 500

    return app

if __name__ == '__main__':
    app = create_app()
    print("="*60)
    print("🚀 Loan Dashboard Flask Application Starting...")
    print("="*60)
    print(f"📍 Server URL: http://127.0.0.1:6000")
    print(f"🔧 Debug Mode: ON")
    print(f"💾 Session Directory: ./flask_session")
    print("="*60)
    print("\nPress CTRL+C to stop the server\n")
    app.run(debug=True, host='127.0.0.1', port=6000)
