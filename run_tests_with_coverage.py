"""
Run Complete Test Suite with Coverage

MUST be run from project root directory!

Usage:
    cd ~/rokomari-ai-pipeline
    python run_tests_with_coverage.py
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd: list, description: str) -> bool:
    """Run a shell command and return success status."""
    print(f"\n{'='*70}")
    print(f"🧪 {description}")
    print(f"{'='*70}\n")
    
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=False,
            text=True
        )
        print(f"\n✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {description} failed with exit code {e.returncode}")
        return False
    except Exception as e:
        print(f"\n❌ {description} failed: {e}")
        return False

def main():
    print("\n" + "="*70)
    print("🚀 ROKOMARI AI PIPELINE - COMPREHENSIVE TEST SUITE")
    print("="*70)
    
    # Check if we're in the right directory
    if not Path("tests/unit").exists():
        print("\n❌ Error: tests/unit directory not found")
        print("   Run this script from the project root directory:")
        print(f"   cd ~/rokomari-ai-pipeline")
        print(f"   python run_tests_with_coverage.py")
        sys.exit(1)
    
    results = {}
    
    # 1. Run unit tests with verbose output
    print("\n🔍 Step 1: Running Unit Tests...")
    results["unit_tests"] = run_command(
        ["pytest", "tests/unit/", "-v", "--tb=short"],
        "Unit Tests"
    )
    
    # 2. Run tests with coverage (terminal report)
    print("\n📊 Step 2: Generating Coverage Report...")
    results["coverage_terminal"] = run_command(
        [
            "pytest",
            "tests/unit/",
            "--cov=src/services",
            "--cov-report=term-missing",
            "--cov-report=term:skip-covered",
            "-v"
        ],
        "Tests with Coverage (Terminal)"
    )
    
    # 3. Generate HTML coverage report
    print("\n📄 Step 3: Generating HTML Report...")
    results["coverage_html"] = run_command(
        [
            "pytest",
            "tests/unit/",
            "--cov=src/services",
            "--cov-report=html",
            "--cov-report=term"
        ],
        "HTML Coverage Report"
    )
    
    # 4. Generate coverage badge data
    print("\n🏷️  Step 4: Generating Coverage JSON...")
    results["coverage_json"] = run_command(
        [
            "pytest",
            "tests/unit/",
            "--cov=src/services",
            "--cov-report=json",
            "-q"
        ],
        "Coverage JSON"
    )
    
    # Print summary
    print("\n" + "="*70)
    print("📊 TEST RESULTS SUMMARY")
    print("="*70 + "\n")
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    # Check if HTML report was generated
    if Path("htmlcov/index.html").exists():
        html_path = Path("htmlcov/index.html").absolute()
        print(f"\n📄 HTML Coverage Report:")
        print(f"   file://{html_path}")
        print("   Open this file in your browser to view detailed coverage")
    
    # Read coverage percentage from JSON
    if Path("coverage.json").exists():
        try:
            import json
            with open("coverage.json") as f:
                cov_data = json.load(f)
                total_coverage = cov_data.get("totals", {}).get("percent_covered", 0)
                print(f"\n📈 Total Coverage: {total_coverage:.1f}%")
                
                if total_coverage >= 70:
                    print(f"   ✅ Meets requirement (70%+)")
                else:
                    print(f"   ⚠️  Below requirement (need 70%+)")
        except Exception as e:
            print(f"\n⚠️  Could not read coverage.json: {e}")
    
    # Overall pass/fail
    all_passed = all(results.values())
    
    print("\n" + "="*70)
    if all_passed:
        print("✅ ALL TESTS PASSED")
    else:
        print("⚠️  SOME TESTS FAILED - Check output above")
    print("="*70 + "\n")
    
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()