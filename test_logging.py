#!/usr/bin/env python3
"""
Test script for the unified logging system
"""

import sys
import os
sys.path.append('.')

from app.common.logging_config import (
    get_logger, health_check, get_log_stats, 
    log_performance, with_correlation_id,
    log_download, log_network, log_exception
)

def test_basic_logging():
    """Test basic logging functionality"""
    print("=== Testing Basic Logging ===")
    logger = get_logger(__name__)
    
    logger.info("This is an info message")
    logger.debug("This is a debug message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    
    print("✓ Basic logging test completed")

def test_specialized_logging():
    """Test specialized logging functions"""
    print("\n=== Testing Specialized Logging ===")
    
    # Test download logging
    log_download("Downloaded file example.jar", size="10MB", url="https://example.com")
    
    # Test network logging
    log_network("HTTP request completed", method="GET", status=200, duration=0.5)
    
    # Test exception logging
    try:
        raise ValueError("This is a test exception")
    except Exception as e:
        log_exception(e, "Test exception occurred", context="testing")
    
    print("✓ Specialized logging test completed")

@log_performance("test_operation")
def test_performance_decorator():
    """Test performance monitoring decorator"""
    print("\n=== Testing Performance Decorator ===")
    import time
    time.sleep(0.1)  # Simulate some work
    return "operation completed"

def test_correlation_id():
    """Test correlation ID functionality"""
    print("\n=== Testing Correlation ID ===")
    logger = get_logger(__name__)
    
    with with_correlation_id("TEST-123") as cid:
        logger.info(f"Message with correlation ID: {cid}")
    
    print("✓ Correlation ID test completed")

def test_health_and_stats():
    """Test health check and statistics"""
    print("\n=== Testing Health Check and Stats ===")
    
    # Health check
    health = health_check()
    print(f"Status: {health['status']}")
    print(f"Handlers: {health['handlers_count']}")
    print(f"Log directory exists: {health['log_directory_exists']}")
    print(f"Writable: {health['writable']}")
    
    # Statistics
    stats = get_log_stats()
    print(f"Uptime: {stats['uptime_seconds']:.2f} seconds")
    print(f"Log counts: {stats['log_counts']}")
    
    print("✓ Health and stats test completed")

def main():
    """Run all tests"""
    print("Starting unified logging system tests...\n")
    
    try:
        test_basic_logging()
        test_specialized_logging()
        test_performance_decorator()
        test_correlation_id()
        test_health_and_stats()
        
        print("\n=== All Tests Completed Successfully ===")
        print("The unified logging system is working correctly!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
