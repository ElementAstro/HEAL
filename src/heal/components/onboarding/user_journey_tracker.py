"""
User Journey Tracking System for HEAL Onboarding

Provides comprehensive analytics and tracking for user journeys to understand
usage patterns and optimize guidance accordingly. Includes privacy-compliant
tracking, pattern analysis, and actionable insights.
"""

import json
import sqlite3
from typing import Dict, List, Any, Optional, Tuple, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import hashlib
import uuid
from collections import defaultdict, Counter

from PySide6.QtCore import QObject, Signal, QTimer
from PySide6.QtWidgets import QApplication

from ...common.logging_config import get_logger

logger = get_logger(__name__)


class EventType(Enum):
    """Types of user journey events"""
    # Onboarding events
    ONBOARDING_STARTED = "onboarding_started"
    ONBOARDING_STEP_COMPLETED = "onboarding_step_completed"
    ONBOARDING_STEP_SKIPPED = "onboarding_step_skipped"
    ONBOARDING_COMPLETED = "onboarding_completed"
    ONBOARDING_ABANDONED = "onboarding_abandoned"
    
    # User interaction events
    FEATURE_DISCOVERED = "feature_discovered"
    FEATURE_USED = "feature_used"
    HELP_ACCESSED = "help_accessed"
    TIP_VIEWED = "tip_viewed"
    TIP_DISMISSED = "tip_dismissed"
    TUTORIAL_STARTED = "tutorial_started"
    TUTORIAL_COMPLETED = "tutorial_completed"
    TUTORIAL_ABANDONED = "tutorial_abandoned"
    
    # Navigation events
    PAGE_VISITED = "page_visited"
    MENU_ACCESSED = "menu_accessed"
    SEARCH_PERFORMED = "search_performed"
    
    # Configuration events
    SETTING_CHANGED = "setting_changed"
    THEME_CHANGED = "theme_changed"
    LAYOUT_CHANGED = "layout_changed"
    
    # Error events
    ERROR_ENCOUNTERED = "error_encountered"
    HELP_REQUESTED = "help_requested"


class UserSegment(Enum):
    """User segments for analytics"""
    NEW_USER = "new_user"
    RETURNING_USER = "returning_user"
    POWER_USER = "power_user"
    STRUGGLING_USER = "struggling_user"
    EXPERT_USER = "expert_user"


@dataclass
class JourneyEvent:
    """Individual journey event"""
    event_id: str
    user_id: str
    session_id: str
    event_type: EventType
    timestamp: datetime
    context: Dict[str, Any]
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'event_id': self.event_id,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'event_type': self.event_type.value,
            'timestamp': self.timestamp.isoformat(),
            'context': json.dumps(self.context),
            'metadata': json.dumps(self.metadata)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JourneyEvent':
        """Create from dictionary"""
        return cls(
            event_id=data['event_id'],
            user_id=data['user_id'],
            session_id=data['session_id'],
            event_type=EventType(data['event_type']),
            timestamp=datetime.fromisoformat(data['timestamp']),
            context=json.loads(data['context']) if data['context'] else {},
            metadata=json.loads(data['metadata']) if data['metadata'] else {}
        )


@dataclass
class UserSession:
    """User session information"""
    session_id: str
    user_id: str
    start_time: datetime
    end_time: Optional[datetime]
    events: List[JourneyEvent]
    user_agent: str
    screen_resolution: str
    
    @property
    def duration(self) -> timedelta:
        """Get session duration"""
        end = self.end_time or datetime.now()
        return end - self.start_time
    
    @property
    def event_count(self) -> int:
        """Get number of events in session"""
        return len(self.events)


@dataclass
class JourneyInsight:
    """Journey analysis insight"""
    insight_type: str
    title: str
    description: str
    impact_level: str  # low, medium, high, critical
    affected_users: int
    confidence_score: float
    recommendations: List[str]
    data: Dict[str, Any]


class UserJourneyDatabase:
    """Database for storing user journey data"""
    
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or Path.home() / ".heal" / "analytics" / "journey.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self) -> None:
        """Initialize database schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS journey_events (
                    event_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    context TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    user_agent TEXT,
                    screen_resolution TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_profiles (
                    user_id TEXT PRIMARY KEY,
                    first_seen TEXT NOT NULL,
                    last_seen TEXT NOT NULL,
                    total_sessions INTEGER DEFAULT 0,
                    total_events INTEGER DEFAULT 0,
                    user_segment TEXT,
                    onboarding_completed BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for better performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_user_id ON journey_events(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_session_id ON journey_events(session_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON journey_events(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_type ON journey_events(event_type)")
    
    def store_event(self, event: JourneyEvent) -> None:
        """Store a journey event"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO journey_events 
                (event_id, user_id, session_id, event_type, timestamp, context, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                event.event_id,
                event.user_id,
                event.session_id,
                event.event_type.value,
                event.timestamp.isoformat(),
                json.dumps(event.context),
                json.dumps(event.metadata)
            ))
    
    def store_session(self, session: UserSession) -> None:
        """Store a user session"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO user_sessions 
                (session_id, user_id, start_time, end_time, user_agent, screen_resolution)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                session.session_id,
                session.user_id,
                session.start_time.isoformat(),
                session.end_time.isoformat() if session.end_time else None,
                session.user_agent,
                session.screen_resolution
            ))
    
    def get_events(self, user_id: Optional[str] = None, 
                   session_id: Optional[str] = None,
                   event_type: Optional[EventType] = None,
                   start_time: Optional[datetime] = None,
                   end_time: Optional[datetime] = None,
                   limit: int = 1000) -> List[JourneyEvent]:
        """Get journey events with filters"""
        query = "SELECT * FROM journey_events WHERE 1=1"
        params = []
        
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        
        if session_id:
            query += " AND session_id = ?"
            params.append(session_id)
        
        if event_type:
            query += " AND event_type = ?"
            params.append(event_type.value)
        
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time.isoformat())
        
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time.isoformat())
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            
            events = []
            for row in cursor.fetchall():
                events.append(JourneyEvent(
                    event_id=row['event_id'],
                    user_id=row['user_id'],
                    session_id=row['session_id'],
                    event_type=EventType(row['event_type']),
                    timestamp=datetime.fromisoformat(row['timestamp']),
                    context=json.loads(row['context']) if row['context'] else {},
                    metadata=json.loads(row['metadata']) if row['metadata'] else {}
                ))
            
            return events
    
    def get_user_sessions(self, user_id: str, limit: int = 100) -> List[UserSession]:
        """Get user sessions"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM user_sessions 
                WHERE user_id = ? 
                ORDER BY start_time DESC 
                LIMIT ?
            """, (user_id, limit))
            
            sessions = []
            for row in cursor.fetchall():
                # Get events for this session
                events = self.get_events(session_id=row['session_id'])
                
                sessions.append(UserSession(
                    session_id=row['session_id'],
                    user_id=row['user_id'],
                    start_time=datetime.fromisoformat(row['start_time']),
                    end_time=datetime.fromisoformat(row['end_time']) if row['end_time'] else None,
                    events=events,
                    user_agent=row['user_agent'] or "",
                    screen_resolution=row['screen_resolution'] or ""
                ))
            
            return sessions
    
    def update_user_profile(self, user_id: str, **kwargs):
        """Update user profile information"""
        with sqlite3.connect(self.db_path) as conn:
            # Get current profile or create new one
            cursor = conn.execute("SELECT * FROM user_profiles WHERE user_id = ?", (user_id,))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing profile
                set_clauses = []
                params = []
                
                for key, value in kwargs.items():
                    if key in ['last_seen', 'total_sessions', 'total_events', 'user_segment', 'onboarding_completed']:
                        set_clauses.append(f"{key} = ?")
                        params.append(value)
                
                if set_clauses:
                    set_clauses.append("updated_at = CURRENT_TIMESTAMP")
                    params.append(user_id)
                    
                    query = f"UPDATE user_profiles SET {', '.join(set_clauses)} WHERE user_id = ?"
                    conn.execute(query, params)
            else:
                # Create new profile
                conn.execute("""
                    INSERT INTO user_profiles 
                    (user_id, first_seen, last_seen, total_sessions, total_events, user_segment, onboarding_completed)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id,
                    kwargs.get('first_seen', datetime.now().isoformat()),
                    kwargs.get('last_seen', datetime.now().isoformat()),
                    kwargs.get('total_sessions', 0),
                    kwargs.get('total_events', 0),
                    kwargs.get('user_segment', UserSegment.NEW_USER.value),
                    kwargs.get('onboarding_completed', False)
                ))


class JourneyAnalyzer:
    """Analyzes user journey data to generate insights"""
    
    def __init__(self, database: UserJourneyDatabase):
        self.database = database
    
    def analyze_onboarding_funnel(self, days: int = 30) -> Dict[str, Any]:
        """Analyze onboarding completion funnel"""
        start_time = datetime.now() - timedelta(days=days)
        
        # Get onboarding events
        started_events = self.database.get_events(
            event_type=EventType.ONBOARDING_STARTED,
            start_time=start_time
        )
        
        completed_events = self.database.get_events(
            event_type=EventType.ONBOARDING_COMPLETED,
            start_time=start_time
        )
        
        abandoned_events = self.database.get_events(
            event_type=EventType.ONBOARDING_ABANDONED,
            start_time=start_time
        )
        
        # Calculate funnel metrics
        started_users = set(event.user_id for event in started_events)
        completed_users = set(event.user_id for event in completed_events)
        abandoned_users = set(event.user_id for event in abandoned_events)
        
        completion_rate = len(completed_users) / len(started_users) if started_users else 0
        abandonment_rate = len(abandoned_users) / len(started_users) if started_users else 0
        
        return {
            'period_days': days,
            'users_started': len(started_users),
            'users_completed': len(completed_users),
            'users_abandoned': len(abandoned_users),
            'completion_rate': completion_rate,
            'abandonment_rate': abandonment_rate,
            'in_progress_users': len(started_users - completed_users - abandoned_users)
        }
    
    def analyze_feature_adoption(self, days: int = 30) -> Dict[str, Any]:
        """Analyze feature discovery and adoption patterns"""
        start_time = datetime.now() - timedelta(days=days)
        
        discovered_events = self.database.get_events(
            event_type=EventType.FEATURE_DISCOVERED,
            start_time=start_time
        )
        
        used_events = self.database.get_events(
            event_type=EventType.FEATURE_USED,
            start_time=start_time
        )
        
        # Analyze by feature
        feature_stats = defaultdict(lambda: {'discovered': 0, 'used': 0, 'users': set()})
        
        for event in discovered_events:
            feature = event.context.get('feature_name', 'unknown')
            feature_stats[feature]['discovered'] += 1
            feature_stats[feature]['users'].add(event.user_id)
        
        for event in used_events:
            feature = event.context.get('feature_name', 'unknown')
            feature_stats[feature]['used'] += 1
            feature_stats[feature]['users'].add(event.user_id)
        
        # Calculate adoption rates
        adoption_data = {}
        for feature, stats in feature_stats.items():
            adoption_rate = stats['used'] / stats['discovered'] if stats['discovered'] > 0 else 0
            adoption_data[feature] = {
                'discovered_count': stats['discovered'],
                'used_count': stats['used'],
                'unique_users': len(stats['users']),
                'adoption_rate': adoption_rate
            }
        
        return adoption_data
    
    def identify_struggling_users(self, days: int = 7) -> List[str]:
        """Identify users who might be struggling"""
        start_time = datetime.now() - timedelta(days=days)
        
        # Get recent events
        recent_events = self.database.get_events(start_time=start_time)
        
        # Analyze user behavior patterns
        user_patterns = defaultdict(lambda: {
            'help_requests': 0,
            'errors': 0,
            'tutorial_abandonments': 0,
            'total_events': 0
        })
        
        for event in recent_events:
            user_id = event.user_id
            user_patterns[user_id]['total_events'] += 1
            
            if event.event_type == EventType.HELP_REQUESTED:
                user_patterns[user_id]['help_requests'] += 1
            elif event.event_type == EventType.ERROR_ENCOUNTERED:
                user_patterns[user_id]['errors'] += 1
            elif event.event_type == EventType.TUTORIAL_ABANDONED:
                user_patterns[user_id]['tutorial_abandonments'] += 1
        
        # Identify struggling users based on patterns
        struggling_users = []
        for user_id, patterns in user_patterns.items():
            if patterns['total_events'] > 0:
                help_ratio = patterns['help_requests'] / patterns['total_events']
                error_ratio = patterns['errors'] / patterns['total_events']
                abandon_ratio = patterns['tutorial_abandonments'] / patterns['total_events']
                
                # User is struggling if they have high ratios of problematic events
                if help_ratio > 0.3 or error_ratio > 0.2 or abandon_ratio > 0.5:
                    struggling_users.append(user_id)
        
        return struggling_users
    
    def generate_insights(self, days: int = 30) -> List[JourneyInsight]:
        """Generate actionable insights from journey data"""
        insights = []
        
        # Onboarding funnel insight
        funnel_data = self.analyze_onboarding_funnel(days)
        if funnel_data['completion_rate'] < 0.7:  # Less than 70% completion
            insights.append(JourneyInsight(
                insight_type="onboarding_completion",
                title="Low Onboarding Completion Rate",
                description=f"Only {funnel_data['completion_rate']:.1%} of users complete onboarding",
                impact_level="high",
                affected_users=funnel_data['users_started'] - funnel_data['users_completed'],
                confidence_score=0.9,
                recommendations=[
                    "Simplify onboarding steps",
                    "Add progress indicators",
                    "Provide skip options for advanced users",
                    "Add contextual help during onboarding"
                ],
                data=funnel_data
            ))
        
        # Feature adoption insight
        adoption_data = self.analyze_feature_adoption(days)
        low_adoption_features = [
            feature for feature, stats in adoption_data.items()
            if stats['adoption_rate'] < 0.3 and stats['discovered_count'] > 10
        ]
        
        if low_adoption_features:
            insights.append(JourneyInsight(
                insight_type="feature_adoption",
                title="Low Feature Adoption",
                description=f"Features with low adoption: {', '.join(low_adoption_features[:3])}",
                impact_level="medium",
                affected_users=sum(adoption_data[f]['unique_users'] for f in low_adoption_features),
                confidence_score=0.8,
                recommendations=[
                    "Improve feature discoverability",
                    "Add feature tutorials",
                    "Simplify feature interfaces",
                    "Provide better feature descriptions"
                ],
                data={'low_adoption_features': low_adoption_features, 'adoption_data': adoption_data}
            ))
        
        # Struggling users insight
        struggling_users = self.identify_struggling_users(days)
        if struggling_users:
            insights.append(JourneyInsight(
                insight_type="user_struggle",
                title="Users Experiencing Difficulties",
                description=f"{len(struggling_users)} users showing signs of struggle",
                impact_level="high",
                affected_users=len(struggling_users),
                confidence_score=0.85,
                recommendations=[
                    "Proactively offer help to struggling users",
                    "Improve error messages and recovery",
                    "Add more contextual guidance",
                    "Consider user experience improvements"
                ],
                data={'struggling_users': struggling_users}
            ))
        
        return insights


class UserJourneyTracker(QObject):
    """Main user journey tracking system"""
    
    # Signals
    event_tracked = Signal(JourneyEvent)
    session_started = Signal(str)  # session_id
    session_ended = Signal(str)    # session_id
    insight_generated = Signal(JourneyInsight)
    
    def __init__(self, database_path: Optional[Path] = None):
        super().__init__()
        
        # Initialize components
        self.database = UserJourneyDatabase(database_path)
        self.analyzer = JourneyAnalyzer(self.database)
        
        # Current session tracking
        self.current_session: Optional[UserSession] = None
        self.current_user_id: Optional[str] = None
        
        # Privacy settings
        self.tracking_enabled = True
        self.anonymize_data = True
        
        # Batch processing
        self.event_queue: List[JourneyEvent] = []
        self.batch_size = 10
        self.batch_timer = QTimer()
        self.batch_timer.timeout.connect(self._process_event_batch)
        self.batch_timer.start(5000)  # Process every 5 seconds
        
        # Insight generation
        self.insight_timer = QTimer()
        self.insight_timer.timeout.connect(self._generate_periodic_insights)
        self.insight_timer.start(3600000)  # Generate insights every hour
        
        logger.info("User journey tracker initialized")
    
    def start_session(self, user_id: str) -> str:
        """Start a new user session"""
        if not self.tracking_enabled:
            return ""
        
        # End current session if exists
        if self.current_session:
            self.end_session()
        
        # Create new session
        session_id = str(uuid.uuid4())
        self.current_user_id = self._anonymize_user_id(user_id) if self.anonymize_data else user_id
        
        # Get system information
        app = QApplication.instance()
        user_agent = f"HEAL/{app.applicationVersion()}" if app else "HEAL/Unknown"
        
        # Get screen resolution
        if app and app.primaryScreen():
            screen = app.primaryScreen()
            screen_resolution = f"{screen.size().width()}x{screen.size().height()}"
        else:
            screen_resolution = "unknown"
        
        self.current_session = UserSession(
            session_id=session_id,
            user_id=self.current_user_id,
            start_time=datetime.now(),
            end_time=None,
            events=[],
            user_agent=user_agent,
            screen_resolution=screen_resolution
        )
        
        # Store session
        self.database.store_session(self.current_session)
        
        # Update user profile
        self.database.update_user_profile(
            self.current_user_id,
            last_seen=datetime.now().isoformat(),
            total_sessions=1  # This will be incremented properly in the database
        )
        
        self.session_started.emit(session_id)
        logger.info(f"Started user session: {session_id}")
        
        return session_id
    
    def end_session(self):
        """End the current user session"""
        if not self.current_session:
            return
        
        self.current_session.end_time = datetime.now()
        self.database.store_session(self.current_session)
        
        # Process any remaining events
        self._process_event_batch()
        
        self.session_ended.emit(self.current_session.session_id)
        logger.info(f"Ended user session: {self.current_session.session_id}")
        
        self.current_session = None
        self.current_user_id = None
    
    def track_event(self, event_type: EventType, context: Optional[Dict[str, Any]] = None,
                   metadata: Optional[Dict[str, Any]] = None):
        """Track a user journey event"""
        if not self.tracking_enabled or not self.current_session:
            return
        
        # Create event
        event = JourneyEvent(
            event_id=str(uuid.uuid4()),
            user_id=self.current_user_id,
            session_id=self.current_session.session_id,
            event_type=event_type,
            timestamp=datetime.now(),
            context=context or {},
            metadata=metadata or {}
        )
        
        # Add to queue for batch processing
        self.event_queue.append(event)
        self.current_session.events.append(event)
        
        # Emit signal
        self.event_tracked.emit(event)
        
        # Process immediately if queue is full
        if len(self.event_queue) >= self.batch_size:
            self._process_event_batch()
    
    def _process_event_batch(self):
        """Process queued events in batch"""
        if not self.event_queue:
            return
        
        try:
            for event in self.event_queue:
                self.database.store_event(event)
            
            # Update user profile with event count
            if self.current_user_id:
                self.database.update_user_profile(
                    self.current_user_id,
                    total_events=len(self.event_queue)
                )
            
            logger.debug(f"Processed {len(self.event_queue)} events")
            self.event_queue.clear()
            
        except Exception as e:
            logger.error(f"Failed to process event batch: {e}")
    
    def _generate_periodic_insights(self):
        """Generate insights periodically"""
        try:
            insights = self.analyzer.generate_insights()
            for insight in insights:
                self.insight_generated.emit(insight)
            
            if insights:
                logger.info(f"Generated {len(insights)} journey insights")
                
        except Exception as e:
            logger.error(f"Failed to generate insights: {e}")
    
    def _anonymize_user_id(self, user_id: str) -> str:
        """Anonymize user ID for privacy"""
        return hashlib.sha256(user_id.encode()).hexdigest()[:16]
    
    def get_user_journey(self, user_id: str, days: int = 30) -> List[JourneyEvent]:
        """Get user journey events"""
        anonymized_id = self._anonymize_user_id(user_id) if self.anonymize_data else user_id
        start_time = datetime.now() - timedelta(days=days)
        return self.database.get_events(user_id=anonymized_id, start_time=start_time)
    
    def get_insights(self, days: int = 30) -> List[JourneyInsight]:
        """Get journey insights"""
        return self.analyzer.generate_insights(days)
    
    def set_tracking_enabled(self, enabled: bool):
        """Enable or disable tracking"""
        self.tracking_enabled = enabled
        logger.info(f"Journey tracking {'enabled' if enabled else 'disabled'}")
    
    def set_anonymization(self, enabled: bool):
        """Enable or disable data anonymization"""
        self.anonymize_data = enabled
        logger.info(f"Data anonymization {'enabled' if enabled else 'disabled'}")
    
    def export_data(self, user_id: Optional[str] = None, 
                   start_date: Optional[datetime] = None,
                   end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Export journey data for analysis"""
        events = self.database.get_events(
            user_id=user_id,
            start_time=start_date,
            end_time=end_date,
            limit=10000
        )
        
        return {
            'export_timestamp': datetime.now().isoformat(),
            'user_id': user_id,
            'date_range': {
                'start': start_date.isoformat() if start_date else None,
                'end': end_date.isoformat() if end_date else None
            },
            'event_count': len(events),
            'events': [event.to_dict() for event in events]
        }
    
    def cleanup_old_data(self, days_to_keep: int = 90):
        """Clean up old journey data"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        with sqlite3.connect(self.database.db_path) as conn:
            # Delete old events
            cursor = conn.execute(
                "DELETE FROM journey_events WHERE timestamp < ?",
                (cutoff_date.isoformat(),)
            )
            deleted_events = cursor.rowcount
            
            # Delete old sessions
            cursor = conn.execute(
                "DELETE FROM user_sessions WHERE start_time < ?",
                (cutoff_date.isoformat(),)
            )
            deleted_sessions = cursor.rowcount
            
            logger.info(f"Cleaned up {deleted_events} events and {deleted_sessions} sessions older than {days_to_keep} days")


# Global journey tracker instance
_journey_tracker: Optional[UserJourneyTracker] = None


def get_journey_tracker() -> UserJourneyTracker:
    """Get global journey tracker instance"""
    global _journey_tracker
    
    if _journey_tracker is None:
        _journey_tracker = UserJourneyTracker()
    
    return _journey_tracker


def initialize_journey_tracking(database_path: Optional[Path] = None) -> UserJourneyTracker:
    """Initialize journey tracking system"""
    global _journey_tracker
    
    _journey_tracker = UserJourneyTracker(database_path)
    logger.info("Journey tracking system initialized")
    
    return _journey_tracker


def shutdown_journey_tracking():
    """Shutdown journey tracking system"""
    global _journey_tracker
    
    if _journey_tracker:
        _journey_tracker.end_session()
        _journey_tracker = None
    
    logger.info("Journey tracking system shutdown")
