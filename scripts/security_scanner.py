#!/usr/bin/env python3
"""
Security scanning utilities for HEAL application.
Provides comprehensive security analysis and vulnerability detection.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


class SecurityScanner:
    """Comprehensive security scanner for the HEAL project."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.src_dir = project_root / "src"
        self.reports_dir = project_root / "security-reports"
        self.reports_dir.mkdir(exist_ok=True)

    def run_bandit_scan(self) -> Dict[str, Any]:
        """Run Bandit security scan on source code."""
        print("Running Bandit security scan...")

        report_file = self.reports_dir / "bandit-report.json"

        try:
            # Install bandit if not available
            subprocess.run([
                sys.executable, "-m", "pip", "install", "bandit[toml]"
            ], check=True, capture_output=True)

            # Run bandit scan
            result = subprocess.run([
                sys.executable, "-m", "bandit",
                "-r", str(self.src_dir),
                "-f", "json",
                "-o", str(report_file),
                "--severity-level", "medium",
                "--confidence-level", "medium"
            ], capture_output=True, text=True)

            # Load and return results
            if report_file.exists():
                with open(report_file, 'r') as f:
                    report: Dict[str, Any] = json.load(f)

                print(
                    f"Bandit scan completed. Found {len(report.get('results', []))} issues.")
                return report
            else:
                print("Bandit scan completed with no output file.")
                return {"results": [], "metrics": {}}

        except subprocess.CalledProcessError as e:
            print(f"Bandit scan failed: {e}")
            return {"error": str(e), "results": []}
        except Exception as e:
            print(f"Error running Bandit: {e}")
            return {"error": str(e), "results": []}

    def run_safety_scan(self) -> Dict:
        """Run Safety scan for known vulnerabilities in dependencies."""
        print("Running Safety vulnerability scan...")

        report_file = self.reports_dir / "safety-report.json"

        try:
            # Install safety if not available
            subprocess.run([
                sys.executable, "-m", "pip", "install", "safety"
            ], check=True, capture_output=True)

            # Run safety check
            result = subprocess.run([
                sys.executable, "-m", "safety", "check",
                "--json", "--output", str(report_file)
            ], capture_output=True, text=True)

            # Load and return results
            if report_file.exists():
                with open(report_file, 'r') as f:
                    report = json.load(f)

                vulnerabilities = len(report) if isinstance(
                    report, list) else 0
                print(
                    f"Safety scan completed. Found {vulnerabilities} vulnerabilities.")
                return {"vulnerabilities": report}
            else:
                print("Safety scan completed with no vulnerabilities found.")
                return {"vulnerabilities": []}

        except subprocess.CalledProcessError as e:
            print(f"Safety scan failed: {e}")
            return {"error": str(e), "vulnerabilities": []}
        except Exception as e:
            print(f"Error running Safety: {e}")
            return {"error": str(e), "vulnerabilities": []}

    def run_pip_audit_scan(self) -> Dict:
        """Run pip-audit scan for dependency vulnerabilities."""
        print("Running pip-audit vulnerability scan...")

        report_file = self.reports_dir / "pip-audit-report.json"

        try:
            # Install pip-audit if not available
            subprocess.run([
                sys.executable, "-m", "pip", "install", "pip-audit"
            ], check=True, capture_output=True)

            # Run pip-audit
            result = subprocess.run([
                sys.executable, "-m", "pip-audit",
                "--format=json", f"--output={report_file}"
            ], capture_output=True, text=True)

            # Load and return results
            if report_file.exists():
                with open(report_file, 'r') as f:
                    report: Dict[str, Any] = json.load(f)

                vulnerabilities = len(report.get("vulnerabilities", []))
                print(
                    f"pip-audit scan completed. Found {vulnerabilities} vulnerabilities.")
                return report
            else:
                print("pip-audit scan completed with no vulnerabilities found.")
                return {"vulnerabilities": []}

        except subprocess.CalledProcessError as e:
            print(f"pip-audit scan failed: {e}")
            return {"error": str(e), "vulnerabilities": []}
        except Exception as e:
            print(f"Error running pip-audit: {e}")
            return {"error": str(e), "vulnerabilities": []}

    def check_secrets(self) -> Dict:
        """Check for potential secrets in the codebase."""
        print("Checking for potential secrets...")

        secrets_patterns = [
            r'(?i)(password|passwd|pwd)\s*[=:]\s*["\'][^"\']+["\']',
            r'(?i)(api[_-]?key|apikey)\s*[=:]\s*["\'][^"\']+["\']',
            r'(?i)(secret[_-]?key|secretkey)\s*[=:]\s*["\'][^"\']+["\']',
            r'(?i)(access[_-]?token|accesstoken)\s*[=:]\s*["\'][^"\']+["\']',
            r'(?i)(private[_-]?key|privatekey)\s*[=:]\s*["\'][^"\']+["\']',
        ]

        findings = []

        for pattern in secrets_patterns:
            try:
                result = subprocess.run([
                    "grep", "-r", "-n", "-E", pattern, str(self.src_dir)
                ], capture_output=True, text=True)

                if result.stdout:
                    for line in result.stdout.strip().split('\n'):
                        if line:
                            file_path, line_num, content = line.split(':', 2)
                            findings.append({
                                "file": file_path,
                                "line": int(line_num),
                                "content": content.strip(),
                                "pattern": pattern
                            })
            except subprocess.CalledProcessError:
                # grep returns non-zero when no matches found
                pass
            except Exception as e:
                print(f"Error checking secrets with pattern {pattern}: {e}")

        print(
            f"Secrets check completed. Found {len(findings)} potential secrets.")
        return {"potential_secrets": findings}

    def check_file_permissions(self) -> Dict:
        """Check for files with overly permissive permissions."""
        print("Checking file permissions...")

        issues = []

        for file_path in self.project_root.rglob("*"):
            if file_path.is_file():
                try:
                    stat = file_path.stat()
                    mode = oct(stat.st_mode)[-3:]  # Get last 3 digits

                    # Check for world-writable files
                    if mode.endswith('2') or mode.endswith('3') or mode.endswith('6') or mode.endswith('7'):
                        issues.append({
                            "file": str(file_path.relative_to(self.project_root)),
                            "permissions": mode,
                            "issue": "World-writable file"
                        })

                    # Check for executable files that shouldn't be
                    if file_path.suffix in ['.py', '.txt', '.md', '.json', '.yml', '.yaml']:
                        if mode.startswith('7') or mode[1] in ['7', '5', '3', '1']:
                            issues.append({
                                "file": str(file_path.relative_to(self.project_root)),
                                "permissions": mode,
                                "issue": "Unnecessary execute permission"
                            })

                except Exception as e:
                    print(f"Error checking permissions for {file_path}: {e}")

        print(f"Permission check completed. Found {len(issues)} issues.")
        return {"permission_issues": issues}

    def generate_security_report(self) -> Dict[str, Any]:
        """Generate comprehensive security report."""
        print("Generating comprehensive security report...")

        report: Dict[str, Any] = {
            "timestamp": subprocess.run([
                "date", "-u", "+%Y-%m-%dT%H:%M:%SZ"
            ], capture_output=True, text=True).stdout.strip(),
            "project": "HEAL",
            "scans": {}
        }

        # Run all security scans
        report["scans"]["bandit"] = self.run_bandit_scan()
        report["scans"]["safety"] = self.run_safety_scan()
        report["scans"]["pip_audit"] = self.run_pip_audit_scan()
        report["scans"]["secrets"] = self.check_secrets()
        report["scans"]["permissions"] = self.check_file_permissions()

        # Calculate summary
        total_issues = 0
        critical_issues = 0

        # Count Bandit issues
        bandit_results = report["scans"]["bandit"].get("results", [])
        total_issues += len(bandit_results)
        critical_issues += len(
            [r for r in bandit_results if r.get("issue_severity") == "HIGH"])

        # Count Safety vulnerabilities
        safety_vulns = report["scans"]["safety"].get("vulnerabilities", [])
        total_issues += len(safety_vulns)
        # All safety issues are considered critical
        critical_issues += len(safety_vulns)

        # Count pip-audit vulnerabilities
        pip_audit_vulns = report["scans"]["pip_audit"].get(
            "vulnerabilities", [])
        total_issues += len(pip_audit_vulns)

        # Count secrets
        secrets = report["scans"]["secrets"].get("potential_secrets", [])
        total_issues += len(secrets)
        critical_issues += len(secrets)  # All secrets are considered critical

        # Count permission issues
        perm_issues = report["scans"]["permissions"].get(
            "permission_issues", [])
        total_issues += len(perm_issues)

        report["summary"] = {
            "total_issues": total_issues,
            "critical_issues": critical_issues,
            "status": "FAIL" if critical_issues > 0 else "PASS"
        }

        # Save comprehensive report
        report_file = self.reports_dir / "security-report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\nSecurity Report Summary:")
        print(f"Total Issues: {total_issues}")
        print(f"Critical Issues: {critical_issues}")
        print(f"Status: {report['summary']['status']}")
        print(f"Report saved to: {report_file}")

        return report

    def print_summary(self, report: Dict) -> None:
        """Print a human-readable summary of the security report."""
        print("\n" + "="*60)
        print("SECURITY SCAN SUMMARY")
        print("="*60)

        summary = report.get("summary", {})
        print(f"Overall Status: {summary.get('status', 'UNKNOWN')}")
        print(f"Total Issues: {summary.get('total_issues', 0)}")
        print(f"Critical Issues: {summary.get('critical_issues', 0)}")

        scans = report.get("scans", {})

        # Bandit results
        bandit = scans.get("bandit", {})
        bandit_issues = len(bandit.get("results", []))
        if bandit_issues > 0:
            print(f"\nBandit (Code Security): {bandit_issues} issues found")
            for result in bandit.get("results", [])[:5]:  # Show first 5
                print(
                    f"  - {result.get('test_name', 'Unknown')}: {result.get('issue_text', 'No description')}")

        # Safety results
        safety = scans.get("safety", {})
        safety_issues = len(safety.get("vulnerabilities", []))
        if safety_issues > 0:
            print(
                f"\nSafety (Dependencies): {safety_issues} vulnerabilities found")
            for vuln in safety.get("vulnerabilities", [])[:5]:  # Show first 5
                if isinstance(vuln, dict):
                    print(
                        f"  - {vuln.get('package', 'Unknown')}: {vuln.get('vulnerability', 'No description')}")

        # Secrets results
        secrets = scans.get("secrets", {})
        secrets_count = len(secrets.get("potential_secrets", []))
        if secrets_count > 0:
            print(f"\nPotential Secrets: {secrets_count} found")
            for secret in secrets.get("potential_secrets", [])[:3]:  # Show first 3
                print(
                    f"  - {secret.get('file', 'Unknown')}: Line {secret.get('line', 0)}")

        # Permission issues
        perms = scans.get("permissions", {})
        perm_count = len(perms.get("permission_issues", []))
        if perm_count > 0:
            print(f"\nPermission Issues: {perm_count} found")
            for issue in perms.get("permission_issues", [])[:3]:  # Show first 3
                print(
                    f"  - {issue.get('file', 'Unknown')}: {issue.get('issue', 'Unknown issue')}")

        print("\n" + "="*60)


def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(description="HEAL Security Scanner")
    parser.add_argument(
        "--scan",
        choices=["all", "bandit", "safety",
                 "pip-audit", "secrets", "permissions"],
        default="all",
        help="Type of security scan to run"
    )
    parser.add_argument(
        "--output",
        choices=["json", "summary", "both"],
        default="both",
        help="Output format"
    )
    parser.add_argument(
        "--fail-on-issues",
        action="store_true",
        help="Exit with non-zero code if issues are found"
    )

    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    scanner = SecurityScanner(project_root)

    if args.scan == "all":
        report = scanner.generate_security_report()
    else:
        # Run individual scans
        if args.scan == "bandit":
            result = scanner.run_bandit_scan()
        elif args.scan == "safety":
            result = scanner.run_safety_scan()
        elif args.scan == "pip-audit":
            result = scanner.run_pip_audit_scan()
        elif args.scan == "secrets":
            result = scanner.check_secrets()
        elif args.scan == "permissions":
            result = scanner.check_file_permissions()

        report = {"scans": {args.scan: result}}

    # Output results
    if args.output in ["json", "both"]:
        print(json.dumps(report, indent=2))

    if args.output in ["summary", "both"]:
        scanner.print_summary(report)

    # Exit with appropriate code
    if args.fail_on_issues:
        summary = report.get("summary", {})
        if summary.get("critical_issues", 0) > 0:
            sys.exit(1)


if __name__ == "__main__":
    main()
