"""
Dashboard Blueprint

Handles routes for the main dashboard view showing loan portfolio overview,
key metrics, and visualizations.
"""
from flask import Blueprint, render_template

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def index():
    """
    Dashboard home page.

    Shows overview of all loans, key metrics, and visualizations.
    This is a placeholder for Phase 4 implementation.
    """
    return render_template('dashboard/index.html')
