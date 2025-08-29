"""
Journey Analytics Dashboard for HEAL Onboarding

Provides a comprehensive dashboard for viewing user journey analytics,
insights, and patterns to help optimize the onboarding experience.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox, QGridLayout,
    QComboBox, QDateEdit, QProgressBar, QTextEdit, QScrollArea, QFrame,
    QSplitter, QListWidget, QListWidgetItem, QCheckBox, QSpinBox
)
from PySide6.QtCore import Qt, QTimer, QThread, Signal, QDate
from PySide6.QtGui import QFont, QPalette, QColor, QPainter, QPen
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QPieSeries, QBarSeries, QBarSet

from .user_journey_tracker import (
    UserJourneyTracker, get_journey_tracker, EventType, JourneyInsight,
    UserSegment, JourneyEvent
)
from ...common.logging_config import get_logger

logger = get_logger(__name__)


class AnalyticsWorker(QThread):
    """Background worker for analytics processing"""
    
    data_ready = Signal(dict)
    insights_ready = Signal(list)
    error_occurred = Signal(str)
    
    def __init__(self, tracker: UserJourneyTracker, days: int = 30):
        super().__init__()
        self.tracker = tracker
        self.days = days
        self.running = True
    
    def run(self):
        """Run analytics processing"""
        try:
            # Generate analytics data
            analytics_data = {
                'onboarding_funnel': self.tracker.analyzer.analyze_onboarding_funnel(self.days),
                'feature_adoption': self.tracker.analyzer.analyze_feature_adoption(self.days),
                'struggling_users': self.tracker.analyzer.identify_struggling_users(7),
                'timestamp': datetime.now().isoformat()
            }
            
            self.data_ready.emit(analytics_data)
            
            # Generate insights
            insights = self.tracker.analyzer.generate_insights(self.days)
            self.insights_ready.emit(insights)
            
        except Exception as e:
            self.error_occurred.emit(str(e))
    
    def stop(self):
        """Stop the worker"""
        self.running = False
        self.quit()
        self.wait()


class MetricCard(QFrame):
    """Card widget for displaying key metrics"""
    
    def __init__(self, title: str, value: str, subtitle: str = "", color: str = "#0078d4"):
        super().__init__()
        self.setFrameStyle(QFrame.Box)
        self.setStyleSheet(f"""
            QFrame {{
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                background-color: white;
                padding: 16px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 12px; color: #666; font-weight: bold;")
        layout.addWidget(title_label)
        
        # Value
        value_label = QLabel(value)
        value_label.setStyleSheet(f"font-size: 24px; color: {color}; font-weight: bold;")
        layout.addWidget(value_label)
        
        # Subtitle
        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setStyleSheet("font-size: 10px; color: #888;")
            layout.addWidget(subtitle_label)
        
        layout.addStretch()


class InsightCard(QFrame):
    """Card widget for displaying insights"""
    
    def __init__(self, insight: JourneyInsight):
        super().__init__()
        self.insight = insight
        self.setFrameStyle(QFrame.Box)
        
        # Color based on impact level
        colors = {
            'low': '#28a745',
            'medium': '#ffc107', 
            'high': '#fd7e14',
            'critical': '#dc3545'
        }
        color = colors.get(insight.impact_level, '#6c757d')
        
        self.setStyleSheet(f"""
            QFrame {{
                border-left: 4px solid {color};
                background-color: white;
                border-radius: 4px;
                padding: 12px;
                margin: 4px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel(insight.title)
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header_layout.addWidget(title_label)
        
        impact_label = QLabel(insight.impact_level.upper())
        impact_label.setStyleSheet(f"color: {color}; font-size: 10px; font-weight: bold;")
        header_layout.addWidget(impact_label)
        
        layout.addLayout(header_layout)
        
        # Description
        desc_label = QLabel(insight.description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666; margin: 8px 0;")
        layout.addWidget(desc_label)
        
        # Affected users and confidence
        stats_layout = QHBoxLayout()
        
        users_label = QLabel(f"Affected Users: {insight.affected_users}")
        users_label.setStyleSheet("font-size: 11px; color: #888;")
        stats_layout.addWidget(users_label)
        
        confidence_label = QLabel(f"Confidence: {insight.confidence_score:.0%}")
        confidence_label.setStyleSheet("font-size: 11px; color: #888;")
        stats_layout.addWidget(confidence_label)
        
        layout.addLayout(stats_layout)
        
        # Recommendations
        if insight.recommendations:
            rec_label = QLabel("Recommendations:")
            rec_label.setStyleSheet("font-weight: bold; font-size: 12px; margin-top: 8px;")
            layout.addWidget(rec_label)
            
            for rec in insight.recommendations[:3]:  # Show top 3
                bullet_label = QLabel(f"• {rec}")
                bullet_label.setStyleSheet("font-size: 11px; color: #666; margin-left: 16px;")
                bullet_label.setWordWrap(True)
                layout.addWidget(bullet_label)


class OnboardingFunnelWidget(QWidget):
    """Widget for displaying onboarding funnel analytics"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the UI"""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Onboarding Funnel Analysis")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 16px;")
        layout.addWidget(title)
        
        # Metrics container
        self.metrics_layout = QHBoxLayout()
        layout.addLayout(self.metrics_layout)
        
        # Funnel visualization placeholder
        self.funnel_chart = QLabel("Funnel chart will be displayed here")
        self.funnel_chart.setStyleSheet("border: 1px dashed #ccc; padding: 40px; text-align: center;")
        self.funnel_chart.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.funnel_chart)
    
    def update_data(self, funnel_data: Dict[str, Any]):
        """Update funnel data"""
        # Clear existing metrics
        for i in reversed(range(self.metrics_layout.count())):
            self.metrics_layout.itemAt(i).widget().setParent(None)
        
        # Add metric cards
        metrics = [
            ("Users Started", str(funnel_data.get('users_started', 0)), "Total users who began onboarding"),
            ("Users Completed", str(funnel_data.get('users_completed', 0)), "Successfully completed onboarding"),
            ("Completion Rate", f"{funnel_data.get('completion_rate', 0):.1%}", "Percentage of users who completed"),
            ("In Progress", str(funnel_data.get('in_progress_users', 0)), "Currently in onboarding process")
        ]
        
        for title, value, subtitle in metrics:
            card = MetricCard(title, value, subtitle)
            self.metrics_layout.addWidget(card)


class FeatureAdoptionWidget(QWidget):
    """Widget for displaying feature adoption analytics"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the UI"""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Feature Adoption Analysis")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 16px;")
        layout.addWidget(title)
        
        # Feature table
        self.feature_table = QTableWidget()
        self.feature_table.setColumnCount(4)
        self.feature_table.setHorizontalHeaderLabels([
            "Feature", "Discovered", "Used", "Adoption Rate"
        ])
        self.feature_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.feature_table)
    
    def update_data(self, adoption_data: Dict[str, Any]):
        """Update adoption data"""
        self.feature_table.setRowCount(len(adoption_data))
        
        for row, (feature, stats) in enumerate(adoption_data.items()):
            self.feature_table.setItem(row, 0, QTableWidgetItem(feature))
            self.feature_table.setItem(row, 1, QTableWidgetItem(str(stats['discovered_count'])))
            self.feature_table.setItem(row, 2, QTableWidgetItem(str(stats['used_count'])))
            self.feature_table.setItem(row, 3, QTableWidgetItem(f"{stats['adoption_rate']:.1%}"))


class InsightsWidget(QWidget):
    """Widget for displaying journey insights"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the UI"""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Journey Insights & Recommendations")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 16px;")
        layout.addWidget(title)
        
        # Scroll area for insights
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarNever)
        
        self.insights_container = QWidget()
        self.insights_layout = QVBoxLayout(self.insights_container)
        self.insights_layout.addStretch()
        
        scroll_area.setWidget(self.insights_container)
        layout.addWidget(scroll_area)
    
    def update_insights(self, insights: List[JourneyInsight]):
        """Update insights display"""
        # Clear existing insights
        for i in reversed(range(self.insights_layout.count() - 1)):  # Keep stretch
            item = self.insights_layout.itemAt(i)
            if item.widget():
                item.widget().setParent(None)
        
        # Add insight cards
        if not insights:
            no_insights = QLabel("No insights available. Check back later as more data is collected.")
            no_insights.setStyleSheet("color: #666; font-style: italic; padding: 20px;")
            no_insights.setAlignment(Qt.AlignCenter)
            self.insights_layout.insertWidget(0, no_insights)
        else:
            for insight in insights:
                card = InsightCard(insight)
                self.insights_layout.insertWidget(self.insights_layout.count() - 1, card)


class JourneyAnalyticsDashboard(QWidget):
    """Main analytics dashboard widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tracker = get_journey_tracker()
        self.analytics_worker = None
        self.setup_ui()
        self.setup_connections()
        
        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(300000)  # Refresh every 5 minutes
        
        # Initial data load
        self.refresh_data()
    
    def setup_ui(self):
        """Setup the dashboard UI"""
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("Journey Analytics Dashboard")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Date range selector
        date_label = QLabel("Analysis Period:")
        header_layout.addWidget(date_label)
        
        self.date_range = QComboBox()
        self.date_range.addItems(["Last 7 days", "Last 30 days", "Last 90 days"])
        self.date_range.setCurrentText("Last 30 days")
        self.date_range.currentTextChanged.connect(self.on_date_range_changed)
        header_layout.addWidget(self.date_range)
        
        # Refresh button
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_data)
        header_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Main content tabs
        self.tab_widget = QTabWidget()
        
        # Overview tab
        self.overview_tab = self.create_overview_tab()
        self.tab_widget.addTab(self.overview_tab, "Overview")
        
        # Onboarding tab
        self.onboarding_widget = OnboardingFunnelWidget()
        self.tab_widget.addTab(self.onboarding_widget, "Onboarding Funnel")
        
        # Features tab
        self.features_widget = FeatureAdoptionWidget()
        self.tab_widget.addTab(self.features_widget, "Feature Adoption")
        
        # Insights tab
        self.insights_widget = InsightsWidget()
        self.tab_widget.addTab(self.insights_widget, "Insights")
        
        layout.addWidget(self.tab_widget)
        
        # Status bar
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #666; font-size: 11px; padding: 4px;")
        layout.addWidget(self.status_label)
    
    def create_overview_tab(self) -> QWidget:
        """Create overview tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Key metrics
        metrics_group = QGroupBox("Key Metrics")
        metrics_layout = QGridLayout(metrics_group)
        
        self.total_users_label = QLabel("0")
        self.total_users_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #0078d4;")
        metrics_layout.addWidget(QLabel("Total Users:"), 0, 0)
        metrics_layout.addWidget(self.total_users_label, 0, 1)
        
        self.active_sessions_label = QLabel("0")
        self.active_sessions_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #28a745;")
        metrics_layout.addWidget(QLabel("Active Sessions:"), 1, 0)
        metrics_layout.addWidget(self.active_sessions_label, 1, 1)
        
        self.completion_rate_label = QLabel("0%")
        self.completion_rate_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #ffc107;")
        metrics_layout.addWidget(QLabel("Completion Rate:"), 2, 0)
        metrics_layout.addWidget(self.completion_rate_label, 2, 1)
        
        layout.addWidget(metrics_group)
        
        # Recent activity
        activity_group = QGroupBox("Recent Activity")
        activity_layout = QVBoxLayout(activity_group)
        
        self.activity_list = QListWidget()
        self.activity_list.setMaximumHeight(200)
        activity_layout.addWidget(self.activity_list)
        
        layout.addWidget(activity_group)
        
        layout.addStretch()
        return widget
    
    def setup_connections(self):
        """Setup signal connections"""
        # Connect to tracker signals
        self.tracker.event_tracked.connect(self.on_event_tracked)
        self.tracker.insight_generated.connect(self.on_insight_generated)
    
    def on_date_range_changed(self, text: str):
        """Handle date range change"""
        self.refresh_data()
    
    def get_analysis_days(self) -> int:
        """Get number of days for analysis based on selection"""
        range_map = {
            "Last 7 days": 7,
            "Last 30 days": 30,
            "Last 90 days": 90
        }
        return range_map.get(self.date_range.currentText(), 30)
    
    def refresh_data(self):
        """Refresh analytics data"""
        if self.analytics_worker and self.analytics_worker.isRunning():
            return
        
        self.refresh_btn.setEnabled(False)
        self.status_label.setText("Loading analytics data...")
        
        # Start analytics worker
        days = self.get_analysis_days()
        self.analytics_worker = AnalyticsWorker(self.tracker, days)
        self.analytics_worker.data_ready.connect(self.on_analytics_data_ready)
        self.analytics_worker.insights_ready.connect(self.on_insights_ready)
        self.analytics_worker.error_occurred.connect(self.on_analytics_error)
        self.analytics_worker.finished.connect(self.on_analytics_finished)
        self.analytics_worker.start()
    
    def on_analytics_data_ready(self, data: Dict[str, Any]):
        """Handle analytics data ready"""
        try:
            # Update overview metrics
            funnel_data = data.get('onboarding_funnel', {})
            self.total_users_label.setText(str(funnel_data.get('users_started', 0)))
            self.completion_rate_label.setText(f"{funnel_data.get('completion_rate', 0):.1%}")
            
            # Update onboarding funnel
            self.onboarding_widget.update_data(funnel_data)
            
            # Update feature adoption
            adoption_data = data.get('feature_adoption', {})
            self.features_widget.update_data(adoption_data)
            
            self.status_label.setText(f"Data updated at {datetime.now().strftime('%H:%M:%S')}")
            
        except Exception as e:
            logger.error(f"Error updating analytics data: {e}")
            self.status_label.setText("Error updating data")
    
    def on_insights_ready(self, insights: List[JourneyInsight]):
        """Handle insights ready"""
        self.insights_widget.update_insights(insights)
    
    def on_analytics_error(self, error: str):
        """Handle analytics error"""
        logger.error(f"Analytics error: {error}")
        self.status_label.setText(f"Error: {error}")
    
    def on_analytics_finished(self):
        """Handle analytics worker finished"""
        self.refresh_btn.setEnabled(True)
        if self.analytics_worker:
            self.analytics_worker.deleteLater()
            self.analytics_worker = None
    
    def on_event_tracked(self, event: JourneyEvent):
        """Handle new event tracked"""
        # Add to recent activity
        activity_text = f"{event.timestamp.strftime('%H:%M:%S')} - {event.event_type.value}"
        if event.context:
            context_info = ", ".join(f"{k}: {v}" for k, v in list(event.context.items())[:2])
            activity_text += f" ({context_info})"
        
        item = QListWidgetItem(activity_text)
        self.activity_list.insertItem(0, item)
        
        # Keep only recent items
        while self.activity_list.count() > 50:
            self.activity_list.takeItem(self.activity_list.count() - 1)
    
    def on_insight_generated(self, insight: JourneyInsight):
        """Handle new insight generated"""
        logger.info(f"New insight generated: {insight.title}")
    
    def closeEvent(self, event):
        """Handle close event"""
        if self.analytics_worker and self.analytics_worker.isRunning():
            self.analytics_worker.stop()
        
        self.refresh_timer.stop()
        super().closeEvent(event)


def show_analytics_dashboard(parent=None) -> JourneyAnalyticsDashboard:
    """Show the analytics dashboard"""
    dashboard = JourneyAnalyticsDashboard(parent)
    dashboard.show()
    return dashboard
