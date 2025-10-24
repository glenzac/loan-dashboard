"""
Visualization utilities for creating charts and graphs using Plotly.
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from typing import List, Dict, Optional
from config.constants import DEFAULT_CHART_HEIGHT


class ChartGenerator:
    """Generate various charts for loan visualization."""

    @staticmethod
    def create_payment_timeline(payments_df: pd.DataFrame) -> go.Figure:
        """
        Create a bar chart showing payment timeline.

        Args:
            payments_df: DataFrame with columns: date, principal, interest

        Returns:
            Plotly Figure object
        """
        if payments_df.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No payment data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig

        fig = go.Figure()

        # Add principal component
        fig.add_trace(go.Bar(
            x=payments_df['date'],
            y=payments_df['principal'],
            name='Principal',
            marker_color='#4CAF50'
        ))

        # Add interest component
        fig.add_trace(go.Bar(
            x=payments_df['date'],
            y=payments_df['interest'],
            name='Interest',
            marker_color='#FF6B6B'
        ))

        fig.update_layout(
            title='Payment Timeline',
            xaxis_title='Date',
            yaxis_title='Amount (₹)',
            barmode='stack',
            height=DEFAULT_CHART_HEIGHT,
            hovermode='x unified'
        )

        return fig

    @staticmethod
    def create_principal_vs_interest_pie(total_principal: float, total_interest: float) -> go.Figure:
        """
        Create a donut chart showing principal vs interest breakdown.

        Args:
            total_principal: Total principal amount
            total_interest: Total interest amount

        Returns:
            Plotly Figure object
        """
        labels = ['Principal', 'Interest']
        values = [total_principal, total_interest]
        colors = ['#4CAF50', '#FF6B6B']

        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.4,
            marker=dict(colors=colors),
            textinfo='label+percent',
            hovertemplate='<b>%{label}</b><br>Amount: ₹%{value:,.2f}<br>Percentage: %{percent}<extra></extra>'
        )])

        fig.update_layout(
            title='Principal vs Interest Breakdown',
            height=DEFAULT_CHART_HEIGHT,
            showlegend=True
        )

        return fig

    @staticmethod
    def create_loan_comparison_bar(loans_data: List[Dict]) -> go.Figure:
        """
        Create a bar chart comparing multiple loans.

        Args:
            loans_data: List of dictionaries with loan_name, principal, interest

        Returns:
            Plotly Figure object
        """
        if not loans_data:
            fig = go.Figure()
            fig.add_annotation(
                text="No loan data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig

        loan_names = [loan['loan_name'] for loan in loans_data]
        principals = [loan['principal'] for loan in loans_data]
        interests = [loan['interest'] for loan in loans_data]

        fig = go.Figure()

        fig.add_trace(go.Bar(
            name='Principal',
            x=loan_names,
            y=principals,
            marker_color='#4CAF50'
        ))

        fig.add_trace(go.Bar(
            name='Interest',
            x=loan_names,
            y=interests,
            marker_color='#FF6B6B'
        ))

        fig.update_layout(
            title='Loan Comparison',
            xaxis_title='Loan',
            yaxis_title='Amount (₹)',
            barmode='group',
            height=DEFAULT_CHART_HEIGHT,
            hovermode='x unified'
        )

        return fig

    @staticmethod
    def create_amortization_curve(schedule_df: pd.DataFrame) -> go.Figure:
        """
        Create an amortization curve showing balance over time.

        Args:
            schedule_df: DataFrame with columns: month, balance, principal, interest

        Returns:
            Plotly Figure object
        """
        if schedule_df.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No schedule data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig

        # Create figure with secondary y-axis
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        # Add outstanding balance line
        fig.add_trace(
            go.Scatter(
                x=schedule_df['month'],
                y=schedule_df['balance'],
                name='Outstanding Balance',
                line=dict(color='#2196F3', width=3),
                fill='tozeroy',
                fillcolor='rgba(33, 150, 243, 0.1)'
            ),
            secondary_y=False
        )

        # Add principal and interest as stacked area
        fig.add_trace(
            go.Scatter(
                x=schedule_df['month'],
                y=schedule_df['principal'],
                name='Principal Payment',
                stackgroup='one',
                fillcolor='rgba(76, 175, 80, 0.5)',
                line=dict(width=0.5, color='#4CAF50')
            ),
            secondary_y=True
        )

        fig.add_trace(
            go.Scatter(
                x=schedule_df['month'],
                y=schedule_df['interest'],
                name='Interest Payment',
                stackgroup='one',
                fillcolor='rgba(255, 107, 107, 0.5)',
                line=dict(width=0.5, color='#FF6B6B')
            ),
            secondary_y=True
        )

        # Update axes
        fig.update_xaxes(title_text="Month")
        fig.update_yaxes(title_text="Outstanding Balance (₹)", secondary_y=False)
        fig.update_yaxes(title_text="Monthly Payment (₹)", secondary_y=True)

        fig.update_layout(
            title='Amortization Schedule',
            height=DEFAULT_CHART_HEIGHT,
            hovermode='x unified'
        )

        return fig

    @staticmethod
    def create_scenario_comparison(scenarios_df: pd.DataFrame) -> go.Figure:
        """
        Create a comparison chart for multiple scenarios.

        Args:
            scenarios_df: DataFrame with columns: scenario_name, total_interest, tenure

        Returns:
            Plotly Figure object
        """
        if scenarios_df.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No scenario data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig

        # Create subplots
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Total Interest Comparison', 'Tenure Comparison'),
            specs=[[{"type": "bar"}, {"type": "bar"}]]
        )

        # Interest comparison
        fig.add_trace(
            go.Bar(
                x=scenarios_df['scenario_name'],
                y=scenarios_df['total_interest'],
                name='Total Interest',
                marker_color='#FF6B6B',
                text=scenarios_df['total_interest'].apply(lambda x: f'₹{x:,.0f}'),
                textposition='auto'
            ),
            row=1, col=1
        )

        # Tenure comparison
        fig.add_trace(
            go.Bar(
                x=scenarios_df['scenario_name'],
                y=scenarios_df['tenure'],
                name='Tenure (months)',
                marker_color='#2196F3',
                text=scenarios_df['tenure'].apply(lambda x: f'{x} mo'),
                textposition='auto'
            ),
            row=1, col=2
        )

        fig.update_layout(
            height=DEFAULT_CHART_HEIGHT,
            showlegend=False
        )

        return fig

    @staticmethod
    def create_loan_progress_bar(
        original_principal: float,
        outstanding_balance: float,
        loan_name: str
    ) -> go.Figure:
        """
        Create a progress bar showing loan completion.

        Args:
            original_principal: Original loan amount
            outstanding_balance: Current outstanding balance
            loan_name: Name of the loan

        Returns:
            Plotly Figure object
        """
        paid = original_principal - outstanding_balance
        percentage = (paid / original_principal * 100) if original_principal > 0 else 0

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=[paid],
            y=[loan_name],
            orientation='h',
            marker=dict(color='#4CAF50'),
            name='Paid',
            text=f'{percentage:.1f}% Complete',
            textposition='inside'
        ))

        fig.add_trace(go.Bar(
            x=[outstanding_balance],
            y=[loan_name],
            orientation='h',
            marker=dict(color='#E0E0E0'),
            name='Outstanding',
            showlegend=False
        ))

        fig.update_layout(
            barmode='stack',
            height=100,
            showlegend=False,
            xaxis=dict(showticklabels=False, showgrid=False),
            yaxis=dict(showticklabels=False),
            margin=dict(l=0, r=0, t=0, b=0),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )

        return fig

    @staticmethod
    def create_monthly_obligation_chart(monthly_data: pd.DataFrame) -> go.Figure:
        """
        Create a chart showing monthly payment obligations.

        Args:
            monthly_data: DataFrame with columns: month, year, total_emi

        Returns:
            Plotly Figure object
        """
        if monthly_data.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No payment data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig

        # Create month-year labels
        monthly_data['period'] = monthly_data.apply(
            lambda row: f"{row['year']}-{row['month']:02d}",
            axis=1
        )

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=monthly_data['period'],
            y=monthly_data['total_emi'],
            mode='lines+markers',
            name='Monthly Payment',
            line=dict(color='#FF6B6B', width=2),
            marker=dict(size=8),
            fill='tozeroy',
            fillcolor='rgba(255, 107, 107, 0.1)'
        ))

        fig.update_layout(
            title='Monthly Payment Obligation',
            xaxis_title='Period',
            yaxis_title='Amount (₹)',
            height=DEFAULT_CHART_HEIGHT,
            hovermode='x unified'
        )

        return fig

    @staticmethod
    def create_interest_rate_history_chart(rate_history_df: pd.DataFrame) -> go.Figure:
        """
        Create a chart showing interest rate changes over time.

        Args:
            rate_history_df: DataFrame with columns: effective_date, interest_rate

        Returns:
            Plotly Figure object
        """
        if rate_history_df.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No rate history available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=rate_history_df['effective_date'],
            y=rate_history_df['interest_rate'],
            mode='lines+markers',
            name='Interest Rate',
            line=dict(color='#9C27B0', width=3, shape='vh'),  # Changed from 'hv' to 'vh'
            marker=dict(size=10, symbol='diamond')
        ))

        fig.update_layout(
            title='Interest Rate History',
            xaxis_title='Date',
            yaxis_title='Interest Rate (%)',
            height=DEFAULT_CHART_HEIGHT,
            hovermode='x unified'
        )

        return fig

    @staticmethod
    def create_payment_status_pie(status_counts: Dict[str, int]) -> go.Figure:
        """
        Create a pie chart showing payment status distribution.

        Args:
            status_counts: Dictionary with status as key and count as value

        Returns:
            Plotly Figure object
        """
        if not status_counts:
            fig = go.Figure()
            fig.add_annotation(
                text="No payment status data",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig

        labels = list(status_counts.keys())
        values = list(status_counts.values())

        color_map = {
            'PAID': '#4CAF50',
            'PENDING': '#FFC107',
            'MISSED': '#FF6B6B'
        }
        colors = [color_map.get(label, '#9E9E9E') for label in labels]

        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            marker=dict(colors=colors),
            textinfo='label+value',
            hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
        )])

        fig.update_layout(
            title='Payment Status Distribution',
            height=DEFAULT_CHART_HEIGHT
        )

        return fig
