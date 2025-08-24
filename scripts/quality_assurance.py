"""
Automated Quality Assurance Pipeline for Module Interface

This script provides comprehensive quality checks including:
- Code quality analysis (pylint, flake8, mypy)
- Security vulnerability scanning
- Unit test execution with coverage
- Performance benchmarking
- Documentation validation
- Dependency analysis
"""

import os
import sys
import subprocess
import json
import time
import argparse
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import sys
import os

# 添加项目根目录到路径以导入统一日志配置
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from app.common.logging_config import get_logger, log_performance, health_check

# 使用统一日志配置
logger = get_logger('quality_assurance')


@dataclass
class QualityResult:
    """Result of a quality check"""
    name: str
    passed: bool
    score: Optional[float]
    issues: List[str]
    details: Dict[str, Any]
    execution_time: float


class QualityChecker:
    """Base class for quality checkers"""
    
    def __init__(self, name: str):
        self.name = name
    
    def check(self, project_path: str) -> QualityResult:
        """Perform quality check"""
        raise NotImplementedError
    
    def is_available(self) -> bool:
        """Check if the checker is available"""
        return True


class PylintChecker(QualityChecker):
    """Pylint code quality checker"""
    
    def __init__(self):
        super().__init__("Pylint")
    
    def is_available(self) -> bool:
        try:
            subprocess.run(['pylint', '--version'], 
                         capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def check(self, project_path: str) -> QualityResult:
        start_time = time.time()
        issues = []
        score = None
        
        try:
            # Run pylint on Python files
            python_files = list(Path(project_path).rglob("*.py"))
            if not python_files:
                return QualityResult(
                    name=self.name,
                    passed=True,
                    score=10.0,
                    issues=["No Python files found"],
                    details={},
                    execution_time=time.time() - start_time
                )
            
            # Create pylint config
            pylint_config = self._create_pylint_config()
            
            cmd = [
                'pylint',
                '--output-format=json',
                '--rcfile', pylint_config,
                '--reports=y'
            ] + [str(f) for f in python_files[:10]]  # Limit to first 10 files
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Parse output
            if result.stdout:
                try:
                    data = json.loads(result.stdout)
                    for item in data:
                        if isinstance(item, dict):
                            issues.append(f"{item.get('path', 'unknown')}:{item.get('line', 0)} - {item.get('message', 'Unknown issue')}")
                except json.JSONDecodeError:
                    pass
            
            # Extract score from stderr
            if result.stderr:
                for line in result.stderr.split('\n'):
                    if 'Your code has been rated at' in line:
                        try:
                            score_str = line.split('rated at ')[1].split('/')[0].strip()
                            score = float(score_str)
                        except (IndexError, ValueError):
                            pass
            
            # Clean up config file
            if os.path.exists(pylint_config):
                os.remove(pylint_config)
            
            passed = score is None or score >= 7.0
            
        except Exception as e:
            issues.append(f"Pylint execution failed: {e}")
            passed = False
        
        return QualityResult(
            name=self.name,
            passed=passed,
            score=score,
            issues=issues,
            details={'command': ' '.join(cmd) if 'cmd' in locals() else 'N/A'},
            execution_time=time.time() - start_time
        )
    
    def _create_pylint_config(self) -> str:
        """Create temporary pylint configuration"""
        config_content = """
[MASTER]
extension-pkg-whitelist=

[MESSAGES CONTROL]
disable=missing-docstring,
        too-few-public-methods,
        too-many-arguments,
        too-many-locals,
        too-many-branches,
        too-many-statements,
        line-too-long

[REPORTS]
output-format=json
reports=yes

[REFACTORING]
max-nested-blocks=5

[BASIC]
good-names=i,j,k,ex,Run,_

[DESIGN]
max-args=7
max-locals=15
max-returns=6
max-branches=12
max-statements=50
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pylintrc', delete=False) as f:
            f.write(config_content)
            return f.name


class Flake8Checker(QualityChecker):
    """Flake8 style checker"""
    
    def __init__(self):
        super().__init__("Flake8")
    
    def is_available(self) -> bool:
        try:
            subprocess.run(['flake8', '--version'], 
                         capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def check(self, project_path: str) -> QualityResult:
        start_time = time.time()
        issues = []
        
        try:
            cmd = [
                'flake8',
                '--max-line-length=100',
                '--ignore=E203,W503',
                '--format=%(path)s:%(row)d:%(col)d: %(code)s %(text)s',
                project_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.stdout:
                issues = result.stdout.strip().split('\n')
                issues = [issue for issue in issues if issue.strip()]
            
            passed = len(issues) == 0
            
        except Exception as e:
            issues.append(f"Flake8 execution failed: {e}")
            passed = False
        
        return QualityResult(
            name=self.name,
            passed=passed,
            score=0.0 if issues else 10.0,
            issues=issues,
            details={'issues_count': len(issues)},
            execution_time=time.time() - start_time
        )


class MypyChecker(QualityChecker):
    """MyPy type checker"""
    
    def __init__(self):
        super().__init__("MyPy")
    
    def is_available(self) -> bool:
        try:
            subprocess.run(['mypy', '--version'], 
                         capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def check(self, project_path: str) -> QualityResult:
        start_time = time.time()
        issues = []
        
        try:
            cmd = [
                'mypy',
                '--ignore-missing-imports',
                '--no-strict-optional',
                project_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.stdout:
                issues = result.stdout.strip().split('\n')
                issues = [issue for issue in issues if issue.strip() and 'error:' in issue]
            
            passed = len(issues) == 0
            
        except Exception as e:
            issues.append(f"MyPy execution failed: {e}")
            passed = False
        
        return QualityResult(
            name=self.name,
            passed=passed,
            score=0.0 if issues else 10.0,
            issues=issues,
            details={'type_errors': len(issues)},
            execution_time=time.time() - start_time
        )


class SecurityChecker(QualityChecker):
    """Security vulnerability checker using bandit"""
    
    def __init__(self):
        super().__init__("Security")
    
    def is_available(self) -> bool:
        try:
            subprocess.run(['bandit', '--version'], 
                         capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def check(self, project_path: str) -> QualityResult:
        start_time = time.time()
        issues = []
        
        try:
            cmd = [
                'bandit',
                '-f', 'json',
                '-r', project_path,
                '-x', '*/tests/*,*/test_*'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.stdout:
                try:
                    data = json.loads(result.stdout)
                    for issue in data.get('results', []):
                        severity = issue.get('issue_severity', 'UNKNOWN')
                        confidence = issue.get('issue_confidence', 'UNKNOWN')
                        text = issue.get('issue_text', 'Unknown issue')
                        filename = issue.get('filename', 'unknown')
                        line_number = issue.get('line_number', 0)
                        
                        issues.append(f"{filename}:{line_number} - {severity}/{confidence}: {text}")
                        
                except json.JSONDecodeError as e:
                    issues.append(f"Failed to parse bandit output: {e}")
            
            # Filter out low severity issues for pass/fail determination
            high_severity_issues = [issue for issue in issues 
                                  if 'HIGH/' in issue or 'MEDIUM/' in issue]
            passed = len(high_severity_issues) == 0
            
        except Exception as e:
            issues.append(f"Security check failed: {e}")
            passed = False
        
        return QualityResult(
            name=self.name,
            passed=passed,
            score=10.0 - min(10.0, len(issues) * 2),
            issues=issues,
            details={'total_issues': len(issues), 'high_severity': len([i for i in issues if 'HIGH/' in i])},
            execution_time=time.time() - start_time
        )


class TestChecker(QualityChecker):
    """Unit test runner with coverage"""
    
    def __init__(self):
        super().__init__("Tests")
    
    def is_available(self) -> bool:
        try:
            subprocess.run([sys.executable, '-m', 'pytest', '--version'], 
                         capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def check(self, project_path: str) -> QualityResult:
        start_time = time.time()
        issues = []
        details = {}
        
        try:
            # Find test files
            test_files = list(Path(project_path).rglob("test_*.py"))
            
            if not test_files:
                return QualityResult(
                    name=self.name,
                    passed=True,
                    score=None,
                    issues=["No test files found"],
                    details={'test_files': 0},
                    execution_time=time.time() - start_time
                )
            
            # Run tests with coverage
            cmd = [
                sys.executable, '-m', 'pytest',
                '--tb=short',
                '--cov=' + project_path,
                '--cov-report=json',
                '--cov-report=term-missing',
                str(project_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=project_path)
            
            # Parse test results
            if result.stdout:
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'failed' in line.lower() and 'passed' in line.lower():
                        details['test_summary'] = line.strip()
                    elif line.startswith('FAILED'):
                        issues.append(line.strip())
            
            # Parse coverage
            coverage_file = os.path.join(project_path, 'coverage.json')
            if os.path.exists(coverage_file):
                try:
                    with open(coverage_file, 'r') as f:
                        coverage_data = json.load(f)
                        details['coverage'] = coverage_data.get('totals', {}).get('percent_covered', 0)
                except Exception as e:
                    issues.append(f"Failed to parse coverage: {e}")
            
            passed = result.returncode == 0 and len(issues) == 0
            coverage_score = details.get('coverage', 0)
            
        except Exception as e:
            issues.append(f"Test execution failed: {e}")
            passed = False
            coverage_score = 0
        
        return QualityResult(
            name=self.name,
            passed=passed,
            score=coverage_score,
            issues=issues,
            details=details,
            execution_time=time.time() - start_time
        )


class PerformanceChecker(QualityChecker):
    """Performance benchmark checker"""
    
    def __init__(self):
        super().__init__("Performance")
    
    def check(self, project_path: str) -> QualityResult:
        start_time = time.time()
        issues = []
        details = {}
        
        try:
            # Run performance benchmarks if available
            benchmark_file = os.path.join(project_path, 'benchmarks.py')
            
            if not os.path.exists(benchmark_file):
                return QualityResult(
                    name=self.name,
                    passed=True,
                    score=None,
                    issues=["No benchmark file found"],
                    details={},
                    execution_time=time.time() - start_time
                )
            
            # Run benchmarks
            cmd = [sys.executable, benchmark_file]
            result = subprocess.run(cmd, capture_output=True, text=True, 
                                  cwd=project_path, timeout=300)
            
            if result.returncode != 0:
                issues.append(f"Benchmark execution failed: {result.stderr}")
            else:
                # Parse benchmark results
                try:
                    for line in result.stdout.split('\n'):
                        if 'benchmark:' in line.lower():
                            details['benchmark_results'] = line.strip()
                except Exception:
                    pass
            
            passed = result.returncode == 0
            
        except subprocess.TimeoutExpired:
            issues.append("Benchmark execution timed out")
            passed = False
        except Exception as e:
            issues.append(f"Performance check failed: {e}")
            passed = False
        
        return QualityResult(
            name=self.name,
            passed=passed,
            score=10.0 if passed else 0.0,
            issues=issues,
            details=details,
            execution_time=time.time() - start_time
        )


class DocumentationChecker(QualityChecker):
    """Documentation quality checker"""
    
    def __init__(self):
        super().__init__("Documentation")
    
    def check(self, project_path: str) -> QualityResult:
        start_time = time.time()
        issues = []
        details = {}
        
        try:
            # Check for essential documentation files
            required_docs = ['README.md', 'docs/']
            found_docs = []
            
            for doc in required_docs:
                doc_path = os.path.join(project_path, doc)
                if os.path.exists(doc_path):
                    found_docs.append(doc)
                else:
                    issues.append(f"Missing documentation: {doc}")
            
            # Check docstring coverage
            python_files = list(Path(project_path).rglob("*.py"))
            total_functions = 0
            documented_functions = 0
            
            for py_file in python_files:
                if 'test' in str(py_file):
                    continue
                    
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                        # Simple docstring detection
                        import ast
                        tree = ast.parse(content)
                        
                        for node in ast.walk(tree):
                            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                                total_functions += 1
                                if ast.get_docstring(node):
                                    documented_functions += 1
                                    
                except Exception as e:
                    issues.append(f"Error analyzing {py_file}: {e}")
            
            docstring_coverage = (documented_functions / total_functions * 100) if total_functions > 0 else 100
            details['docstring_coverage'] = docstring_coverage
            details['documented_functions'] = documented_functions
            details['total_functions'] = total_functions
            details['found_docs'] = found_docs
            
            # Determine pass/fail
            passed = (len(found_docs) >= 1 and docstring_coverage >= 50)
            
        except Exception as e:
            issues.append(f"Documentation check failed: {e}")
            passed = False
        
        return QualityResult(
            name=self.name,
            passed=passed,
            score=details.get('docstring_coverage', 0),
            issues=issues,
            details=details,
            execution_time=time.time() - start_time
        )


class DependencyChecker(QualityChecker):
    """Dependency analysis checker"""
    
    def __init__(self):
        super().__init__("Dependencies")
    
    def is_available(self) -> bool:
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'check'], 
                         capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def check(self, project_path: str) -> QualityResult:
        start_time = time.time()
        issues = []
        details = {}
        
        try:
            # Check for requirements.txt
            req_file = os.path.join(project_path, 'requirements.txt')
            if not os.path.exists(req_file):
                issues.append("No requirements.txt found")
            else:
                # Parse requirements
                with open(req_file, 'r') as f:
                    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                    details['requirements_count'] = len(requirements)
            
            # Check for dependency conflicts
            cmd = [sys.executable, '-m', 'pip', 'check']
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.stdout:
                conflicts = result.stdout.strip().split('\n')
                conflicts = [c for c in conflicts if c.strip()]
                if conflicts:
                    issues.extend(conflicts)
            
            # Check for outdated packages
            try:
                cmd = [sys.executable, '-m', 'pip', 'list', '--outdated', '--format=json']
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.stdout:
                    outdated = json.loads(result.stdout)
                    details['outdated_packages'] = len(outdated)
                    if len(outdated) > 0:
                        issues.append(f"{len(outdated)} packages are outdated")
            except Exception:
                pass
            
            passed = len([issue for issue in issues if 'conflict' in issue.lower()]) == 0
            
        except Exception as e:
            issues.append(f"Dependency check failed: {e}")
            passed = False
        
        return QualityResult(
            name=self.name,
            passed=passed,
            score=10.0 if passed else 5.0,
            issues=issues,
            details=details,
            execution_time=time.time() - start_time
        )


class QualityAssurancePipeline:
    """Main QA pipeline orchestrator"""
    
    def __init__(self, project_path: str):
        self.project_path = project_path
        self.checkers = [
            PylintChecker(),
            Flake8Checker(),
            MypyChecker(),
            SecurityChecker(),
            TestChecker(),
            PerformanceChecker(),
            DocumentationChecker(),
            DependencyChecker()
        ]
        
        # Filter to available checkers
        self.checkers = [checker for checker in self.checkers if checker.is_available()]
        
        logger.info(f"Initialized QA pipeline with {len(self.checkers)} checkers")
    
    def run_all_checks(self) -> Dict[str, QualityResult]:
        """Run all quality checks"""
        results = {}
        
        logger.info(f"Starting quality checks for {self.project_path}")
        
        for checker in self.checkers:
            logger.info(f"Running {checker.name} check...")
            
            try:
                result = checker.check(self.project_path)
                results[checker.name] = result
                
                status = "PASSED" if result.passed else "FAILED"
                logger.info(f"{checker.name}: {status} ({result.execution_time:.2f}s)")
                
            except Exception as e:
                logger.error(f"Error running {checker.name}: {e}")
                results[checker.name] = QualityResult(
                    name=checker.name,
                    passed=False,
                    score=None,
                    issues=[f"Checker failed: {e}"],
                    details={},
                    execution_time=0.0
                )
        
        return results
    
    def run_specific_checks(self, checker_names: List[str]) -> Dict[str, QualityResult]:
        """Run specific quality checks"""
        results = {}
        
        for checker in self.checkers:
            if checker.name.lower() in [name.lower() for name in checker_names]:
                logger.info(f"Running {checker.name} check...")
                results[checker.name] = checker.check(self.project_path)
        
        return results
    
    def generate_report(self, results: Dict[str, QualityResult], 
                       output_file: Optional[str] = None) -> str:
        """Generate comprehensive quality report"""
        report_lines = []
        
        # Header
        report_lines.append("=" * 80)
        report_lines.append("QUALITY ASSURANCE REPORT")
        report_lines.append("=" * 80)
        report_lines.append(f"Project: {self.project_path}")
        report_lines.append(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        # Summary
        total_checks = len(results)
        passed_checks = sum(1 for r in results.values() if r.passed)
        
        report_lines.append("SUMMARY")
        report_lines.append("-" * 40)
        report_lines.append(f"Total Checks: {total_checks}")
        report_lines.append(f"Passed: {passed_checks}")
        report_lines.append(f"Failed: {total_checks - passed_checks}")
        report_lines.append(f"Success Rate: {passed_checks/total_checks*100:.1f}%")
        report_lines.append("")
        
        # Overall score
        scores = [r.score for r in results.values() if r.score is not None]
        if scores:
            overall_score = sum(scores) / len(scores)
            report_lines.append(f"Overall Score: {overall_score:.1f}/10.0")
        report_lines.append("")
        
        # Detailed results
        report_lines.append("DETAILED RESULTS")
        report_lines.append("-" * 40)
        
        for name, result in results.items():
            status = "✓ PASSED" if result.passed else "✗ FAILED"
            score_str = f" ({result.score:.1f}/10.0)" if result.score is not None else ""
            
            report_lines.append(f"{name}: {status}{score_str}")
            report_lines.append(f"  Execution Time: {result.execution_time:.2f}s")
            
            if result.issues:
                report_lines.append(f"  Issues ({len(result.issues)}):")
                for issue in result.issues[:10]:  # Limit to first 10 issues
                    report_lines.append(f"    - {issue}")
                if len(result.issues) > 10:
                    report_lines.append(f"    ... and {len(result.issues) - 10} more")
            
            if result.details:
                report_lines.append(f"  Details: {result.details}")
            
            report_lines.append("")
        
        # Recommendations
        report_lines.append("RECOMMENDATIONS")
        report_lines.append("-" * 40)
        
        failed_checks = [name for name, result in results.items() if not result.passed]
        if failed_checks:
            report_lines.append("Failed checks that need attention:")
            for check in failed_checks:
                report_lines.append(f"  - {check}")
        else:
            report_lines.append("All checks passed! Great job!")
        
        report_lines.append("")
        report_lines.append("=" * 80)
        
        report = "\n".join(report_lines)
        
        # Save to file if specified
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report)
            logger.info(f"Report saved to {output_file}")
        
        return report
    
    def export_json_report(self, results: Dict[str, QualityResult], 
                          output_file: str) -> None:
        """Export results as JSON"""
        json_data = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'project_path': self.project_path,
            'summary': {
                'total_checks': len(results),
                'passed_checks': sum(1 for r in results.values() if r.passed),
                'success_rate': sum(1 for r in results.values() if r.passed) / len(results) * 100
            },
            'results': {}
        }
        
        for name, result in results.items():
            json_data['results'][name] = {
                'passed': result.passed,
                'score': result.score,
                'issues': result.issues,
                'details': result.details,
                'execution_time': result.execution_time
            }
        
        with open(output_file, 'w') as f:
            json.dump(json_data, f, indent=2)
        
        logger.info(f"JSON report saved to {output_file}")


def main():
    """Main entry point for QA pipeline"""
    parser = argparse.ArgumentParser(description="Automated Quality Assurance Pipeline")
    parser.add_argument("project_path", help="Path to the project to analyze")
    parser.add_argument("--checks", nargs="+", help="Specific checks to run", 
                       choices=['pylint', 'flake8', 'mypy', 'security', 'tests', 
                              'performance', 'documentation', 'dependencies'])
    parser.add_argument("--output", "-o", help="Output file for report")
    parser.add_argument("--json", help="JSON output file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        # Enable debug logging
        logger.info("Debug mode enabled")
    
    # Validate project path
    if not os.path.exists(args.project_path):
        logger.error(f"Project path does not exist: {args.project_path}")
        sys.exit(1)
    
    # Initialize pipeline
    pipeline = QualityAssurancePipeline(args.project_path)
    
    # Run checks
    if args.checks:
        results = pipeline.run_specific_checks(args.checks)
    else:
        results = pipeline.run_all_checks()
    
    # Generate reports
    report = pipeline.generate_report(results, args.output)
    print(report)
    
    if args.json:
        pipeline.export_json_report(results, args.json)
    
    # Exit with appropriate code
    failed_checks = sum(1 for r in results.values() if not r.passed)
    sys.exit(failed_checks)


if __name__ == "__main__":
    main()
