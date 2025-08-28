#!/usr/bin/env python3
"""
NutriGuard Test Runner
Comprehensive test execution with coverage reporting and CI/CD integration
"""

import os
import sys
import subprocess
import json
import time
from pathlib import Path
from datetime import datetime
import argparse

class TestRunner:
    """Advanced test runner with reporting and CI/CD integration"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'errors': 0,
            'skipped': 0,
            'coverage': 0.0,
            'duration': 0.0,
            'test_files': []
        }
    
    def run_tests(self, test_pattern='test_*.py', coverage=True, verbose=True):
        """Run test suite with optional coverage"""
        print("🧪 NutriGuard Test Suite")
        print("=" * 50)
        
        start_time = time.time()
        
        try:
            # Discover and run tests
            if coverage:
                self._run_with_coverage(test_pattern, verbose)
            else:
                self._run_without_coverage(test_pattern, verbose)
            
            # Calculate duration
            self.test_results['duration'] = time.time() - start_time
            
            # Generate reports
            self._generate_reports()
            
            # Print summary
            self._print_summary()
            
            # Return exit code
            return 0 if self.test_results['failed'] == 0 and self.test_results['errors'] == 0 else 1
            
        except Exception as e:
            print(f"❌ Test execution failed: {e}")
            return 1
    
    def _run_with_coverage(self, test_pattern, verbose):
        """Run tests with coverage reporting"""
        print("📊 Running tests with coverage...")
        
        # Install coverage if not available
        self._ensure_coverage_installed()
        
        # Run tests with coverage
        cmd = [
            sys.executable, '-m', 'coverage', 'run',
            '--source', '.',
            '--omit', 'test_*.py,venv/*,env/*',
            '-m', 'unittest', 'discover',
            '-s', str(self.project_root),
            '-p', test_pattern
        ]
        
        if verbose:
            cmd.append('-v')
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Parse test results
        self._parse_unittest_output(result.stderr)
        
        # Generate coverage report
        self._generate_coverage_report()
    
    def _run_without_coverage(self, test_pattern, verbose):
        """Run tests without coverage"""
        print("🏃 Running tests...")
        
        cmd = [
            sys.executable, '-m', 'unittest', 'discover',
            '-s', str(self.project_root),
            '-p', test_pattern
        ]
        
        if verbose:
            cmd.append('-v')
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Parse test results
        self._parse_unittest_output(result.stderr)
    
    def _ensure_coverage_installed(self):
        """Ensure coverage package is installed"""
        try:
            import coverage
        except ImportError:
            print("📦 Installing coverage package...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'coverage'], check=True)
    
    def _parse_unittest_output(self, output):
        """Parse unittest output to extract results"""
        lines = output.strip().split('\n')
        
        for line in lines:
            if line.startswith('Ran '):
                # Extract total tests
                parts = line.split()
                self.test_results['total_tests'] = int(parts[1])
            elif 'FAILED' in line or 'ERRORS' in line:
                # Parse failures and errors
                if 'failures=' in line:
                    failures = int(line.split('failures=')[1].split(',')[0].split(')')[0])
                    self.test_results['failed'] = failures
                if 'errors=' in line:
                    errors = int(line.split('errors=')[1].split(',')[0].split(')')[0])
                    self.test_results['errors'] = errors
            elif line == 'OK':
                # All tests passed
                self.test_results['passed'] = self.test_results['total_tests']
        
        # Calculate passed tests
        if self.test_results['passed'] == 0:
            self.test_results['passed'] = (
                self.test_results['total_tests'] - 
                self.test_results['failed'] - 
                self.test_results['errors']
            )
    
    def _generate_coverage_report(self):
        """Generate coverage report"""
        try:
            # Generate coverage report
            result = subprocess.run([
                sys.executable, '-m', 'coverage', 'report', '--show-missing'
            ], capture_output=True, text=True)
            
            # Extract coverage percentage
            lines = result.stdout.split('\n')
            for line in lines:
                if line.startswith('TOTAL'):
                    parts = line.split()
                    if len(parts) >= 4:
                        coverage_str = parts[3].rstrip('%')
                        self.test_results['coverage'] = float(coverage_str)
                        break
            
            # Generate HTML report
            subprocess.run([
                sys.executable, '-m', 'coverage', 'html',
                '--directory', 'htmlcov'
            ], capture_output=True)
            
            # Generate XML report (for CI/CD)
            subprocess.run([
                sys.executable, '-m', 'coverage', 'xml'
            ], capture_output=True)
            
        except Exception as e:
            print(f"⚠️ Coverage report generation failed: {e}")
    
    def _generate_reports(self):
        """Generate test reports"""
        # Create reports directory
        reports_dir = self.project_root / 'reports'
        reports_dir.mkdir(exist_ok=True)
        
        # Generate JSON report
        json_report = reports_dir / 'test_results.json'
        with open(json_report, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        # Generate JUnit XML report (for CI/CD)
        self._generate_junit_xml(reports_dir / 'junit.xml')
        
        print(f"📄 Reports generated in {reports_dir}")
    
    def _generate_junit_xml(self, output_file):
        """Generate JUnit XML report for CI/CD integration"""
        xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<testsuites name="NutriGuard Test Suite" 
            tests="{self.test_results['total_tests']}" 
            failures="{self.test_results['failed']}" 
            errors="{self.test_results['errors']}" 
            time="{self.test_results['duration']:.2f}">
    <testsuite name="nutriguard.tests" 
               tests="{self.test_results['total_tests']}" 
               failures="{self.test_results['failed']}" 
               errors="{self.test_results['errors']}" 
               time="{self.test_results['duration']:.2f}">
        <!-- Individual test cases would be listed here in a full implementation -->
    </testsuite>
</testsuites>"""
        
        with open(output_file, 'w') as f:
            f.write(xml_content)
    
    def _print_summary(self):
        """Print test execution summary"""
        print("\n" + "=" * 50)
        print("📋 TEST EXECUTION SUMMARY")
        print("=" * 50)
        print(f"Total Tests:     {self.test_results['total_tests']}")
        print(f"Passed:          {self.test_results['passed']} ✅")
        print(f"Failed:          {self.test_results['failed']} ❌")
        print(f"Errors:          {self.test_results['errors']} 💥")
        print(f"Duration:        {self.test_results['duration']:.2f}s ⏱️")
        
        if self.test_results['coverage'] > 0:
            print(f"Coverage:        {self.test_results['coverage']:.1f}% 📊")
        
        # Success rate
        if self.test_results['total_tests'] > 0:
            success_rate = (self.test_results['passed'] / self.test_results['total_tests']) * 100
            print(f"Success Rate:    {success_rate:.1f}% 🎯")
        
        print("=" * 50)
        
        # Status message
        if self.test_results['failed'] == 0 and self.test_results['errors'] == 0:
            print("🎉 All tests passed!")
        else:
            print("⚠️ Some tests failed. Check the output above for details.")
        
        # Coverage message
        if self.test_results['coverage'] >= 90:
            print("🏆 Excellent test coverage!")
        elif self.test_results['coverage'] >= 80:
            print("👍 Good test coverage")
        elif self.test_results['coverage'] >= 70:
            print("⚠️ Test coverage could be improved")
        else:
            print("🚨 Low test coverage - consider adding more tests")

def run_specific_tests():
    """Run specific test categories"""
    test_categories = {
        'auth': 'test_suite.py::TestAuthentication',
        'ai': 'test_suite.py::TestNutritionAnalysis test_suite.py::TestCropPrediction',
        'payment': 'test_suite.py::TestPaymentIntegration',
        'security': 'test_suite.py::TestSecurity',
        'api': 'test_suite.py::TestDashboard',
        'models': 'test_suite.py::TestDataModels'
    }
    
    print("Available test categories:")
    for category, description in test_categories.items():
        print(f"  {category}: {description}")
    
    return test_categories

def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(description='NutriGuard Test Runner')
    parser.add_argument(
        '--no-coverage', 
        action='store_true',
        help='Run tests without coverage reporting'
    )
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Run tests in quiet mode'
    )
    parser.add_argument(
        '--pattern', '-p',
        default='test_*.py',
        help='Test file pattern (default: test_*.py)'
    )
    parser.add_argument(
        '--category', '-c',
        help='Run specific test category'
    )
    parser.add_argument(
        '--list-categories',
        action='store_true',
        help='List available test categories'
    )
    
    args = parser.parse_args()
    
    if args.list_categories:
        run_specific_tests()
        return 0
    
    # Create test runner
    runner = TestRunner()
    
    # Run tests
    exit_code = runner.run_tests(
        test_pattern=args.pattern,
        coverage=not args.no_coverage,
        verbose=not args.quiet
    )
    
    return exit_code

if __name__ == '__main__':
    sys.exit(main())