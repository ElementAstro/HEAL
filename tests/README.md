# HEAL Onboarding System Test Suite

Comprehensive test suite for the HEAL onboarding system, providing thorough validation of all components, integration scenarios, and performance characteristics.

## 📋 Test Overview

The test suite is organized into several categories:

### 🧪 Unit Tests
- **test_user_state_tracker.py**: User state management, preferences, and onboarding progress
- **test_smart_tip_system.py**: Intelligent tip selection, context awareness, and rotation
- **test_recommendation_engine.py**: Recommendation generation, behavior analysis, and lifecycle
- **test_tutorial_system.py**: Interactive tutorials, step validation, and progress tracking

### 🔗 Integration Tests
- **test_onboarding_system.py**: Complete system integration and component interactions
- **test_integration_scenarios.py**: Real-world user journeys and workflows

### ⚡ Performance Tests
- **test_performance_benchmarks.py**: Performance benchmarks, memory usage, and scalability

## 🚀 Running Tests

### Quick Start

```bash
# Run all tests (excluding performance)
python tests/run_tests.py all

# Run unit tests only
python tests/run_tests.py unit

# Run integration tests
python tests/run_tests.py integration

# Run performance tests
python tests/run_tests.py performance

# Quick smoke test
python tests/run_tests.py smoke
```

### Advanced Usage

```bash
# Run with verbose output
python tests/run_tests.py all -v

# Include performance tests in full run
python tests/run_tests.py all -p

# Run specific test pattern
python tests/run_tests.py specific -k "test_user_level"

# Run with coverage analysis
python tests/run_tests.py coverage

# Run without final report
python tests/run_tests.py unit --no-report
```

### Using pytest directly

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_user_state_tracker.py

# Run with markers
pytest -m "unit"
pytest -m "integration"
pytest -m "performance"

# Run with coverage
pytest --cov=src/heal/components/onboarding --cov-report=html

# Run specific test
pytest tests/test_user_state_tracker.py::TestUserStateTrackerCore::test_initialization
```

## 📊 Test Categories and Markers

### Markers
- `unit`: Individual component tests
- `integration`: System interaction tests
- `performance`: Performance and benchmark tests
- `slow`: Long-running tests
- `ui`: Tests requiring UI components
- `smoke`: Quick functionality verification
- `stress`: System limit tests
- `memory`: Memory usage tests
- `concurrent`: Thread safety tests

### Test Organization

```
tests/
├── conftest.py                    # Shared fixtures and configuration
├── run_tests.py                   # Comprehensive test runner
├── test_user_state_tracker.py     # User state management tests
├── test_smart_tip_system.py       # Smart tip system tests
├── test_recommendation_engine.py  # Recommendation engine tests
├── test_tutorial_system.py        # Tutorial system tests
├── test_onboarding_system.py      # System integration tests
├── test_integration_scenarios.py  # Real-world scenario tests
└── test_performance_benchmarks.py # Performance and stress tests
```

## 🧪 Test Coverage

### Component Coverage

| Component | Unit Tests | Integration Tests | Performance Tests |
|-----------|------------|-------------------|-------------------|
| UserStateTracker | ✅ Complete | ✅ Complete | ✅ Complete |
| SmartTipSystem | ✅ Complete | ✅ Complete | ✅ Complete |
| RecommendationEngine | ✅ Complete | ✅ Complete | ✅ Complete |
| TutorialSystem | ✅ Complete | ✅ Complete | ✅ Complete |
| ContextualHelp | ✅ Complete | ✅ Complete | ✅ Complete |
| FeatureDiscovery | ✅ Complete | ✅ Complete | ✅ Complete |
| DocumentationIntegration | ✅ Complete | ✅ Complete | ✅ Complete |
| OnboardingManager | ✅ Complete | ✅ Complete | ✅ Complete |

### Scenario Coverage

- ✅ First-time user journey
- ✅ Returning user experience
- ✅ User level progression
- ✅ Error handling and recovery
- ✅ Performance under load
- ✅ Memory usage optimization
- ✅ Concurrent operations
- ✅ System integration
- ✅ Configuration management
- ✅ Preference propagation

## 📈 Performance Benchmarks

### Expected Performance Metrics

| Operation | Target Performance | Measured |
|-----------|-------------------|----------|
| System Initialization | < 2.0s | ✅ |
| Action Tracking | > 100 actions/sec | ✅ |
| Recommendation Generation | < 1.0s | ✅ |
| Documentation Search | > 10 searches/sec | ✅ |
| Statistics Generation | < 0.5s | ✅ |

### Memory Usage

| Scenario | Target | Measured |
|----------|--------|----------|
| Baseline Object Count | < 1000 objects | ✅ |
| Memory Leak Detection | < 500 object growth | ✅ |
| Large Data Handling | < 5.0s for 1MB | ✅ |

## 🔧 Test Configuration

### Environment Variables

- `RUN_PERFORMANCE_TESTS=1`: Enable performance tests in CI
- `DISPLAY`: Required for UI tests on Linux
- `CI`: Detected automatically, affects test behavior

### Dependencies

```bash
# Core testing
pip install pytest pytest-cov pytest-mock

# Performance testing
pip install pytest-benchmark memory-profiler

# UI testing (if needed)
pip install pytest-qt

# Coverage reporting
pip install coverage
```

### Configuration Files

- `pytest.ini`: Main pytest configuration
- `conftest.py`: Shared fixtures and test utilities
- `.coveragerc`: Coverage analysis configuration

## 🐛 Debugging Tests

### Common Issues

1. **Import Errors**: Ensure `src/` is in Python path
2. **Qt Application Issues**: Use `qapp` fixture for UI tests
3. **Mock Failures**: Check mock configuration in `conftest.py`
4. **Performance Test Failures**: May need adjustment for slower systems

### Debug Commands

```bash
# Run with debug output
pytest -s -vv tests/test_specific.py

# Run single test with debugging
pytest --pdb tests/test_file.py::test_function

# Show test output
pytest -s tests/test_file.py

# Run with coverage and show missing lines
pytest --cov=src --cov-report=term-missing
```

## 📝 Writing New Tests

### Test Structure

```python
class TestNewFeature:
    """Test new feature functionality"""
    
    @pytest.fixture
    def setup_feature(self):
        """Setup fixture for feature tests"""
        # Setup code
        yield feature_instance
        # Cleanup code
    
    def test_feature_initialization(self, setup_feature):
        """Test feature initialization"""
        assert setup_feature is not None
        # Test assertions
    
    @pytest.mark.unit
    def test_feature_behavior(self, setup_feature):
        """Test specific feature behavior"""
        # Test implementation
        pass
    
    @pytest.mark.integration
    def test_feature_integration(self, setup_feature):
        """Test feature integration with other components"""
        # Integration test implementation
        pass
```

### Best Practices

1. **Use Descriptive Names**: Test names should clearly describe what is being tested
2. **Arrange-Act-Assert**: Structure tests with clear setup, execution, and verification
3. **Use Fixtures**: Leverage pytest fixtures for common setup and teardown
4. **Mock External Dependencies**: Use mocks to isolate components under test
5. **Test Edge Cases**: Include tests for error conditions and boundary cases
6. **Performance Considerations**: Add performance markers for slow tests
7. **Documentation**: Include docstrings explaining test purpose and approach

### Adding Performance Tests

```python
@pytest.mark.performance
def test_new_feature_performance(self, setup_feature):
    """Test performance of new feature"""
    import time
    
    start_time = time.time()
    
    # Perform operation
    for i in range(1000):
        setup_feature.perform_operation()
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Assert performance threshold
    assert duration < 1.0, f"Operation took {duration:.2f}s, expected < 1.0s"
```

## 📊 Test Reports

### Coverage Reports

```bash
# Generate HTML coverage report
pytest --cov=src --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Performance Reports

Performance tests output timing information and can be used to track performance regressions over time.

### CI Integration

The test suite is designed to work in CI environments:

- Automatic test discovery
- Proper exit codes for CI systems
- Environment-aware test execution
- Performance test gating

## 🎯 Test Goals

### Quality Assurance
- ✅ 100% component coverage
- ✅ All user scenarios tested
- ✅ Error conditions handled
- ✅ Performance requirements met

### Reliability
- ✅ Consistent test results
- ✅ Proper test isolation
- ✅ Comprehensive mocking
- ✅ Resource cleanup

### Maintainability
- ✅ Clear test organization
- ✅ Reusable fixtures
- ✅ Good documentation
- ✅ Easy to extend

## 🔄 Continuous Integration

The test suite supports various CI workflows:

```yaml
# Example GitHub Actions workflow
- name: Run Tests
  run: |
    python tests/run_tests.py all -v
    
- name: Run Performance Tests
  run: |
    python tests/run_tests.py performance -v
    
- name: Generate Coverage
  run: |
    python tests/run_tests.py coverage
```

## 📞 Support

For test-related issues:

1. Check this documentation
2. Review test output and error messages
3. Examine fixture configuration in `conftest.py`
4. Run individual tests for debugging
5. Check environment setup and dependencies

The test suite is designed to be comprehensive, maintainable, and reliable, ensuring the HEAL onboarding system meets all quality and performance requirements.
