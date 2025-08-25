"""
Settings Search Engine
Provides powerful search and filtering capabilities for settings
"""

import re
import time
from typing import Dict, List, Any, Optional, Set, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache
from difflib import SequenceMatcher
from PySide6.QtCore import QObject, Signal, QTimer
from PySide6.QtWidgets import QWidget

from app.common.logging_config import get_logger


class SearchType(Enum):
    """Types of search operations"""
    EXACT = "exact"
    FUZZY = "fuzzy"
    KEYWORD = "keyword"
    REGEX = "regex"
    SEMANTIC = "semantic"


class FilterType(Enum):
    """Types of filters"""
    CATEGORY = "category"
    TYPE = "type"
    RECENTLY_CHANGED = "recently_changed"
    FAVORITES = "favorites"
    CUSTOM = "custom"


@dataclass
class SettingItem:
    """Represents a searchable setting item"""
    key: str
    title: str
    description: str
    category: str
    setting_type: str
    value: Any
    widget: Optional[QWidget] = None
    keywords: List[str] = field(default_factory=list)
    last_modified: float = field(default_factory=time.time)
    is_favorite: bool = False
    is_advanced: bool = False
    search_weight: float = 1.0
    
    def __post_init__(self):
        """Generate additional search keywords"""
        if not self.keywords:
            self.keywords = self._generate_keywords()
    
    def _generate_keywords(self) -> List[str]:
        """Generate search keywords from title and description"""
        keywords = []
        
        # Add words from title
        title_words = re.findall(r'\w+', self.title.lower())
        keywords.extend(title_words)
        
        # Add words from description
        desc_words = re.findall(r'\w+', self.description.lower())
        keywords.extend(desc_words)
        
        # Add category and type
        keywords.append(self.category.lower())
        keywords.append(self.setting_type.lower())
        
        # Remove duplicates and short words
        keywords = list(set(word for word in keywords if len(word) > 2))
        
        return keywords


@dataclass
class SearchResult:
    """Represents a search result"""
    item: SettingItem
    score: float
    match_type: SearchType
    matched_fields: List[str]
    highlighted_text: str = ""


@dataclass
class SearchFilter:
    """Represents a search filter"""
    filter_type: FilterType
    value: Any
    operator: str = "equals"  # equals, contains, greater_than, less_than, etc.
    enabled: bool = True


class SettingsSearchEngine(QObject):
    """Advanced search engine for settings"""
    
    # Signals
    search_completed = Signal(list)  # List[SearchResult]
    search_started = Signal(str)     # query
    index_updated = Signal(int)      # item_count
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger('settings_search', module='SettingsSearchEngine')
        
        # Search index
        self.items: Dict[str, SettingItem] = {}
        self.keyword_index: Dict[str, Set[str]] = {}  # keyword -> set of item keys
        self.category_index: Dict[str, Set[str]] = {}  # category -> set of item keys
        self.type_index: Dict[str, Set[str]] = {}     # type -> set of item keys
        
        # Search configuration
        self.fuzzy_threshold = 0.6
        self.max_results = 50
        self.search_weights = {
            'title': 3.0,
            'description': 2.0,
            'keywords': 1.5,
            'category': 1.0,
            'type': 0.5
        }
        
        # Real-time search timer
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._execute_delayed_search)
        self.pending_query = ""
        self.pending_filters = []
        
        self.logger.info("Settings search engine initialized")
    
    def add_setting(self, item: SettingItem) -> None:
        """Add a setting to the search index"""
        self.items[item.key] = item
        
        # Update keyword index
        for keyword in item.keywords:
            if keyword not in self.keyword_index:
                self.keyword_index[keyword] = set()
            self.keyword_index[keyword].add(item.key)
        
        # Update category index
        if item.category not in self.category_index:
            self.category_index[item.category] = set()
        self.category_index[item.category].add(item.key)
        
        # Update type index
        if item.setting_type not in self.type_index:
            self.type_index[item.setting_type] = set()
        self.type_index[item.setting_type].add(item.key)
        
        self.logger.debug(f"Added setting to search index: {item.key}")
    
    def remove_setting(self, key: str) -> None:
        """Remove a setting from the search index"""
        if key not in self.items:
            return
        
        item = self.items[key]
        
        # Remove from keyword index
        for keyword in item.keywords:
            if keyword in self.keyword_index:
                self.keyword_index[keyword].discard(key)
                if not self.keyword_index[keyword]:
                    del self.keyword_index[keyword]
        
        # Remove from category index
        if item.category in self.category_index:
            self.category_index[item.category].discard(key)
            if not self.category_index[item.category]:
                del self.category_index[item.category]
        
        # Remove from type index
        if item.setting_type in self.type_index:
            self.type_index[item.setting_type].discard(key)
            if not self.type_index[item.setting_type]:
                del self.type_index[item.setting_type]
        
        del self.items[key]
        self.logger.debug(f"Removed setting from search index: {key}")
    
    def update_setting(self, item: SettingItem) -> None:
        """Update a setting in the search index"""
        if item.key in self.items:
            self.remove_setting(item.key)
        self.add_setting(item)
    
    def search(self, query: str, filters: List[SearchFilter] = None, 
               search_type: SearchType = SearchType.FUZZY) -> List[SearchResult]:
        """Perform a search with optional filters"""
        if not query.strip() and not filters:
            return []
        
        self.search_started.emit(query)
        start_time = time.time()
        
        try:
            # Get candidate items based on filters
            candidates = self._apply_filters(filters or [])
            
            # Perform search on candidates
            if query.strip():
                results = self._search_items(query, candidates, search_type)
            else:
                # No query, just return filtered items
                results = [
                    SearchResult(
                        item=self.items[key],
                        score=1.0,
                        match_type=SearchType.EXACT,
                        matched_fields=['filter']
                    )
                    for key in candidates
                ]
            
            # Sort by score and limit results
            results.sort(key=lambda r: r.score, reverse=True)
            results = results[:self.max_results]
            
            search_time = time.time() - start_time
            self.logger.debug(f"Search completed in {search_time:.3f}s, {len(results)} results")
            
            self.search_completed.emit(results)
            return results
            
        except Exception as e:
            self.logger.error(f"Search error: {e}")
            return []
    
    def search_realtime(self, query: str, filters: List[SearchFilter] = None, 
                       delay_ms: int = 300) -> None:
        """Perform real-time search with debouncing"""
        self.pending_query = query
        self.pending_filters = filters or []
        
        # Restart timer for debouncing
        self.search_timer.start(delay_ms)
    
    def _execute_delayed_search(self) -> None:
        """Execute the delayed search"""
        self.search(self.pending_query, self.pending_filters)
    
    def _apply_filters(self, filters: List[SearchFilter]) -> Set[str]:
        """Apply filters to get candidate item keys"""
        if not filters:
            return set(self.items.keys())
        
        candidates = set(self.items.keys())
        
        for filter_obj in filters:
            if not filter_obj.enabled:
                continue
            
            filtered_keys = self._apply_single_filter(filter_obj)
            candidates &= filtered_keys
        
        return candidates
    
    def _apply_single_filter(self, filter_obj: SearchFilter) -> Set[str]:
        """Apply a single filter"""
        if filter_obj.filter_type == FilterType.CATEGORY:
            return self.category_index.get(filter_obj.value, set())
        
        elif filter_obj.filter_type == FilterType.TYPE:
            return self.type_index.get(filter_obj.value, set())
        
        elif filter_obj.filter_type == FilterType.RECENTLY_CHANGED:
            threshold = time.time() - filter_obj.value  # value is seconds ago
            return {
                key for key, item in self.items.items()
                if item.last_modified > threshold
            }
        
        elif filter_obj.filter_type == FilterType.FAVORITES:
            return {
                key for key, item in self.items.items()
                if item.is_favorite == filter_obj.value
            }
        
        elif filter_obj.filter_type == FilterType.CUSTOM:
            # Custom filter with lambda function
            if callable(filter_obj.value):
                return {
                    key for key, item in self.items.items()
                    if filter_obj.value(item)
                }
        
        return set()
    
    def _search_items(self, query: str, candidates: Set[str], 
                     search_type: SearchType) -> List[SearchResult]:
        """Search within candidate items"""
        results = []
        query_lower = query.lower()
        
        for key in candidates:
            item = self.items[key]
            
            if search_type == SearchType.EXACT:
                result = self._exact_search(item, query_lower)
            elif search_type == SearchType.FUZZY:
                result = self._fuzzy_search(item, query_lower)
            elif search_type == SearchType.KEYWORD:
                result = self._keyword_search(item, query_lower)
            elif search_type == SearchType.REGEX:
                result = self._regex_search(item, query)
            else:
                result = self._fuzzy_search(item, query_lower)  # Default to fuzzy
            
            if result:
                results.append(result)
        
        return results
    
    def _exact_search(self, item: SettingItem, query: str) -> Optional[SearchResult]:
        """Perform exact string matching"""
        score = 0.0
        matched_fields = []
        
        # Check title
        if query in item.title.lower():
            score += self.search_weights['title']
            matched_fields.append('title')
        
        # Check description
        if query in item.description.lower():
            score += self.search_weights['description']
            matched_fields.append('description')
        
        # Check keywords
        for keyword in item.keywords:
            if query in keyword:
                score += self.search_weights['keywords']
                matched_fields.append('keywords')
                break
        
        if score > 0:
            return SearchResult(
                item=item,
                score=score * item.search_weight,
                match_type=SearchType.EXACT,
                matched_fields=matched_fields,
                highlighted_text=self._highlight_matches(item, query)
            )
        
        return None
    
    @lru_cache(maxsize=1000)
    def _fuzzy_search(self, item: SettingItem, query: str) -> Optional[SearchResult]:
        """Perform fuzzy string matching"""
        score = 0.0
        matched_fields = []
        
        # Check title
        title_ratio = SequenceMatcher(None, query, item.title.lower()).ratio()
        if title_ratio >= self.fuzzy_threshold:
            score += self.search_weights['title'] * title_ratio
            matched_fields.append('title')
        
        # Check description
        desc_ratio = SequenceMatcher(None, query, item.description.lower()).ratio()
        if desc_ratio >= self.fuzzy_threshold:
            score += self.search_weights['description'] * desc_ratio
            matched_fields.append('description')
        
        # Check keywords
        best_keyword_ratio = 0.0
        for keyword in item.keywords:
            ratio = SequenceMatcher(None, query, keyword).ratio()
            if ratio > best_keyword_ratio:
                best_keyword_ratio = ratio
        
        if best_keyword_ratio >= self.fuzzy_threshold:
            score += self.search_weights['keywords'] * best_keyword_ratio
            matched_fields.append('keywords')
        
        if score > 0:
            return SearchResult(
                item=item,
                score=score * item.search_weight,
                match_type=SearchType.FUZZY,
                matched_fields=matched_fields,
                highlighted_text=self._highlight_matches(item, query)
            )
        
        return None
    
    def _keyword_search(self, item: SettingItem, query: str) -> Optional[SearchResult]:
        """Perform keyword-based search"""
        query_words = set(re.findall(r'\w+', query))
        item_words = set(item.keywords)
        
        # Find matching keywords
        matches = query_words & item_words
        if not matches:
            return None
        
        # Calculate score based on match ratio
        match_ratio = len(matches) / len(query_words)
        score = self.search_weights['keywords'] * match_ratio
        
        return SearchResult(
            item=item,
            score=score * item.search_weight,
            match_type=SearchType.KEYWORD,
            matched_fields=['keywords'],
            highlighted_text=self._highlight_matches(item, query)
        )
    
    def _regex_search(self, item: SettingItem, pattern: str) -> Optional[SearchResult]:
        """Perform regex pattern matching"""
        try:
            regex = re.compile(pattern, re.IGNORECASE)
            score = 0.0
            matched_fields = []
            
            # Check title
            if regex.search(item.title):
                score += self.search_weights['title']
                matched_fields.append('title')
            
            # Check description
            if regex.search(item.description):
                score += self.search_weights['description']
                matched_fields.append('description')
            
            if score > 0:
                return SearchResult(
                    item=item,
                    score=score * item.search_weight,
                    match_type=SearchType.REGEX,
                    matched_fields=matched_fields,
                    highlighted_text=self._highlight_matches(item, pattern)
                )
        
        except re.error:
            # Invalid regex pattern
            pass
        
        return None
    
    def _highlight_matches(self, item: SettingItem, query: str) -> str:
        """Generate highlighted text for matches"""
        # Simple highlighting - can be enhanced with HTML/rich text
        text = f"{item.title}: {item.description}"
        highlighted = re.sub(
            f"({re.escape(query)})",
            r"**\1**",
            text,
            flags=re.IGNORECASE
        )
        return highlighted
    
    def get_suggestions(self, partial_query: str, limit: int = 10) -> List[str]:
        """Get search suggestions based on partial query"""
        suggestions = []
        partial_lower = partial_query.lower()
        
        # Get suggestions from keywords
        for keyword in self.keyword_index.keys():
            if keyword.startswith(partial_lower):
                suggestions.append(keyword)
        
        # Get suggestions from categories
        for category in self.category_index.keys():
            if category.lower().startswith(partial_lower):
                suggestions.append(category)
        
        # Sort by relevance and limit
        suggestions.sort(key=lambda s: (len(s), s))
        return suggestions[:limit]
    
    def get_filter_options(self) -> Dict[str, List[str]]:
        """Get available filter options"""
        return {
            'categories': list(self.category_index.keys()),
            'types': list(self.type_index.keys()),
            'recent_periods': ['1 hour', '1 day', '1 week', '1 month']
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get search engine statistics"""
        return {
            'total_items': len(self.items),
            'total_keywords': len(self.keyword_index),
            'categories': len(self.category_index),
            'types': len(self.type_index),
            'favorites': sum(1 for item in self.items.values() if item.is_favorite),
            'advanced_settings': sum(1 for item in self.items.values() if item.is_advanced)
        }
    
    def clear_index(self) -> None:
        """Clear the search index"""
        self.items.clear()
        self.keyword_index.clear()
        self.category_index.clear()
        self.type_index.clear()
        self.index_updated.emit(0)
        self.logger.info("Search index cleared")
    
    def rebuild_index(self, items: List[SettingItem]) -> None:
        """Rebuild the search index with new items"""
        self.clear_index()
        
        for item in items:
            self.add_setting(item)
        
        self.index_updated.emit(len(items))
        self.logger.info(f"Search index rebuilt with {len(items)} items")
