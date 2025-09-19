#!/usr/bin/env python3
"""
Comprehensive test runner for AI Executive Suite

This script provides various testing options including unit tests,
integration tests, performance tests, and security tests.
"""

import os
import sys
import subprocess
import argparse
import time
from pathlib import Path


def run_command(command, capture_output=False):
    """Run a shell command and return the result"""
    try:
        if capture_output:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True,
                check=True
            )
            return result.stdout, result.stderr
        else:
            result = subprocess.run(command, shell=True, check=True)
            return result.returncode == 0
    except subprocess.CalledProcessError as e:
        if capture_output:
            return None, str(e)
        return False


def setup_test_environment():
    """Set up the test environment"""
    print("Setting up test environment...")
    
    # Set environment variables
    os.environ['TESTING'] = 'True'
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
    os.environ['REDIS_URL'] = 'redis://localhost:6379/1'
    os.environ['OPENAI_API_KEY'] = 'test-key'
    
    # Create necessary directories
    Path('htmlcov').mkdir(exist_ok=True)
    Path('test-reports').mkdir(exist_ok=True)
    
    print("✓ Test environment set up")


def run_unit_tests(verbose=False, coverage=True, fail_fast=False):
    """Run unit tests"""
    print("\n" + "="*50)
    print("RUNNING UNIT TESTS")
    print("="*50)
    
    cmd_parts = ['python', '-m', 'pytest', 'tests/']
    
    # Add markers for unit tests
    cmd_parts.extend(['-m', 'not integration and not performance and not security'])
    
    if verbose:
        cmd_parts.append('-v')
    
    if coverage:
        cmd_parts.extend([
            '--cov=services',
            '--cov=models', 
            '--cov=routes',
            '--cov=utils',
            '--cov=ai_ceo',
            '--cov-report=html:htmlcov',
            '--cov-report=term-missing',
            '--cov-report=xml:test-reports/coverage.xml'
        ])
    
    if fail_fast:
        cmd_parts.append('-x')
    
    # Add JUnit XML output for CI/CD
    cmd_parts.extend(['--junitxml=test-reports/unit-tests.xml'])
    
    command = ' '.join(cmd_parts)
    print(f"Running: {command}")
    
    start_time = time.time()
    success = run_command(command)
    end_time = time.time()
    
    if success:
        print(f"✓ Unit tests passed in {end_time - start_time:.2f} seconds")
    else:
        print(f"✗ Unit tests failed after {end_time - start_time:.2f} seconds")
    
    return success


def run_integration_tests(verbose=False):
    """Run integration tests"""
    print("\n" + "="*50)
    print("RUNNING INTEGRATION TESTS")
    print("="*50)
    
    cmd_parts = ['python', '-m', 'pytest', 'tests/integration/', '-m', 'integration']
    
    if verbose:
        cmd_parts.append('-v')
    
    # Add integration-specific options
    cmd_parts.extend([
        '--tb=short',
        '--maxfail=10'  # Allow more failures for integration tests
    ])
    
    # Add JUnit XML output
    cmd_parts.extend(['--junitxml=test-reports/integration-tests.xml'])
    
    command = ' '.join(cmd_parts)
    print(f"Running: {command}")
    
    start_time = time.time()
    success = run_command(command)
    end_time = time.time()
    
    if success:
        print(f"✓ Integration tests passed in {end_time - start_time:.2f} seconds")
    else:
        print(f"✗ Integration tests failed after {end_time - start_time:.2f} seconds")
    
    return success


def run_performance_tests(verbose=False):
    """Run performance tests"""
    print("\n" + "="*50)
    print("RUNNING PERFORMANCE TESTS")
    print("="*50)
    
    cmd_parts = ['python', '-m', 'pytest', 'tests/performance/', '-m', 'performance']
    
    if verbose:
        cmd_parts.append('-v')
    
    # Add performance-specific options
    cmd_parts.extend([
        '--tb=short',
        '-x'  # Stop on first failure for performance tests
    ])
    
    # Add JUnit XML output
    cmd_parts.extend(['--junitxml=test-reports/performance-tests.xml'])
    
    command = ' '.join(cmd_parts)
    print(f"Running: {command}")
    
    start_time = time.time()
    success = run_command(command)
    end_time = time.time()
    
    if success:
        print(f"✓ Performance tests passed in {end_time - start_time:.2f} seconds")
    else:
        print(f"✗ Performance tests failed after {end_time - start_time:.2f} seconds")
    
    return success


def run_security_tests(verbose=False):
    """Run security tests"""
    print("\n" + "="*50)
    print("RUNNING SECURITY TESTS")
    print("="*50)
    
    cmd_parts = ['python', '-m', 'pytest', 'tests/security/', '-m', 'security']
    
    if verbose:
        cmd_parts.append('-v')
    
    # Add security-specific options
    cmd_parts.extend([
        '--tb=short',
        '--maxfail=5'  # Stop after 5 failures for security tests
    ])
    
    # Add JUnit XML output
    cmd_parts.extend(['--junitxml=test-reports/security-tests.xml'])
    
    command = ' '.join(cmd_parts)
    print(f"Running: {command}")
    
    start_time = time.time()
    success = run_command(command)
    end_time = time.time()
    
    if success:
        print(f"✓ Security tests passed in {end_time - start_time:.2f} seconds")
    else:
        print(f"✗ Security tests failed after {end_time - start_time:.2f} seconds")
    
    return success


def run_specific_test(test_path, verbose=False):
    """Run a specific test file or test function"""
    print(f"\n" + "="*50)
    print(f"RUNNING SPECIFIC TEST: {test_path}")
    print("="*50)
    
    cmd_parts = ['python', '-m', 'pytest', test_path]
    
    if verbose:
        cmd_parts.append('-v')
    
    command = ' '.join(cmd_parts)
    print(f"Running: {command}")
    
    start_time = time.time()
    success = run_command(command)
    end_time = time.time()
    
    if success:
        print(f"✓ Test passed in {end_time - start_time:.2f} seconds")
    else:
        print(f"✗ Test failed after {end_time - start_time:.2f} seconds")
    
    return success


def check_test_coverage():
    """Check and report test coverage"""
    print("\n" + "="*50)
    print("CHECKING TEST COVERAGE")
    print("="*50)
    
    # Generate coverage report
    stdout, stderr = run_command('python -m coverage report --show-missing', capture_output=True)
    
    if stdout:
        print(stdout)
        
        # Extract coverage percentage
        lines = stdout.split('\n')
        total_line = [line for line in lines if line.startswith('TOTAL')]
        if total_line:
            coverage_str = total_line[0].split()[-1]
            try:
                coverage_pct = int(coverage_str.rstrip('%'))
                print(f"\nOverall test coverage: {coverage_pct}%")
                
                if coverage_pct >= 90:
                    print("✓ Excellent test coverage!")
                elif coverage_pct >= 80:
                    print("✓ Good test coverage")
                elif coverage_pct >= 70:
                    print("⚠ Moderate test coverage - consider adding more tests")
                else:
                    print("✗ Low test coverage - more tests needed")
                
                return coverage_pct
            except ValueError:
                pass
    
    if stderr:
        print(f"Coverage check error: {stderr}")
    
    return None


def run_linting():
    """Run code linting"""
    print("\n" + "="*50)
    print("RUNNING CODE LINTING")
    print("="*50)
    
    # Run flake8
    print("Running flake8...")
    flake8_success = run_command('python -m flake8 services/ models.py routes/ utils/ ai_ceo/ --max-line-length=120 --ignore=E203,W503')
    
    # Run black check
    print("Running black check...")
    black_success = run_command('python -m black --check services/ models.py routes/ utils/ ai_ceo/')
    
    # Run mypy
    print("Running mypy...")
    mypy_success = run_command('python -m mypy services/ --ignore-missing-imports')
    
    if flake8_success and black_success and mypy_success:
        print("✓ All linting checks passed")
        return True
    else:
        print("✗ Some linting checks failed")
        return False


def generate_test_report():
    """Generate a comprehensive test report"""
    print("\n" + "="*50)
    print("GENERATING TEST REPORT")
    print("="*50)
    
    report_path = Path('test-reports/test-summary.txt')
    
    with open(report_path, 'w') as f:
        f.write("AI Executive Suite Test Report\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Check if test result files exist
        test_files = [
            'unit-tests.xml',
            'integration-tests.xml', 
            'performance-tests.xml',
            'security-tests.xml'
        ]
        
        for test_file in test_files:
            test_path = Path(f'test-reports/{test_file}')
            if test_path.exists():
                f.write(f"✓ {test_file} - Generated\n")
            else:
                f.write(f"✗ {test_file} - Not found\n")
        
        # Coverage report
        coverage_path = Path('test-reports/coverage.xml')
        if coverage_path.exists():
            f.write("✓ coverage.xml - Generated\n")
        else:
            f.write("✗ coverage.xml - Not found\n")
        
        f.write(f"\nHTML Coverage Report: htmlcov/index.html\n")
    
    print(f"✓ Test report generated: {report_path}")


def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(description='AI Executive Suite Test Runner')
    parser.add_argument('--unit', action='store_true', help='Run unit tests')
    parser.add_argument('--integration', action='store_true', help='Run integration tests')
    parser.add_argument('--performance', action='store_true', help='Run performance tests')
    parser.add_argument('--security', action='store_true', help='Run security tests')
    parser.add_argument('--all', action='store_true', help='Run all tests')
    parser.add_argument('--coverage', action='store_true', help='Check test coverage')
    parser.add_argument('--lint', action='store_true', help='Run code linting')
    parser.add_argument('--test', type=str, help='Run specific test file or function')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--fail-fast', '-x', action='store_true', help='Stop on first failure')
    parser.add_argument('--no-coverage', action='store_true', help='Skip coverage reporting')
    
    args = parser.parse_args()
    
    # Set up test environment
    setup_test_environment()
    
    success_count = 0
    total_count = 0
    
    # Run specific test if requested
    if args.test:
        success = run_specific_test(args.test, args.verbose)
        return 0 if success else 1
    
    # Run linting if requested
    if args.lint:
        total_count += 1
        if run_linting():
            success_count += 1
    
    # Run unit tests
    if args.unit or args.all:
        total_count += 1
        if run_unit_tests(args.verbose, not args.no_coverage, args.fail_fast):
            success_count += 1
    
    # Run integration tests
    if args.integration or args.all:
        total_count += 1
        if run_integration_tests(args.verbose):
            success_count += 1
    
    # Run performance tests
    if args.performance or args.all:
        total_count += 1
        if run_performance_tests(args.verbose):
            success_count += 1
    
    # Run security tests
    if args.security or args.all:
        total_count += 1
        if run_security_tests(args.verbose):
            success_count += 1
    
    # Check coverage if requested
    if args.coverage:
        check_test_coverage()
    
    # Generate test report
    if total_count > 0:
        generate_test_report()
    
    # Print summary
    if total_count > 0:
        print("\n" + "="*50)
        print("TEST SUMMARY")
        print("="*50)
        print(f"Passed: {success_count}/{total_count}")
        
        if success_count == total_count:
            print("✓ All tests passed!")
            return 0
        else:
            print("✗ Some tests failed")
            return 1
    else:
        print("No tests specified. Use --help for options.")
        return 1


if __name__ == '__main__':
    sys.exit(main())