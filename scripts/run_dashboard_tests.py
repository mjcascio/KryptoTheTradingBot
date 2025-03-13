#!/usr/bin/env python3
"""
Dashboard Test Runner

This script runs all the dashboard tests and monitoring tools,
and generates a comprehensive report on the dashboard's health and performance.
"""

import os
import sys
import json
import time
import logging
import unittest
import requests
import datetime
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/dashboard_tests.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import test modules
try:
    from tests.test_dashboard import TestDashboardAPI, TestDashboardDataFunctions, TestDashboardFileOperations
    TESTS_AVAILABLE = True
except ImportError:
    TESTS_AVAILABLE = False
    logger.warning("Dashboard tests not found. Test suite will be limited.")

# Import validation utilities if available
try:
    from utils.data_validator import validate_api_response, validate_dashboard_data
    VALIDATION_ENABLED = True
except ImportError:
    VALIDATION_ENABLED = False
    logger.warning("Data validation utilities not found. Validation will be skipped.")

# Import monitoring utilities if available
try:
    from utils.dashboard_monitor import DashboardMonitor
    MONITORING_ENABLED = True
except ImportError:
    MONITORING_ENABLED = False
    logger.warning("Dashboard monitoring utilities not found. Monitoring will be skipped.")

class DashboardTestRunner:
    """
    Test runner for the dashboard
    """
    
    def __init__(self, dashboard_url="http://localhost:5001"):
        """
        Initialize the test runner
        
        Args:
            dashboard_url: URL of the dashboard
        """
        self.dashboard_url = dashboard_url
        self.results = {
            'timestamp': datetime.datetime.now().isoformat(),
            'dashboard_url': dashboard_url,
            'tests': {
                'unit_tests': {
                    'run': False,
                    'success': False,
                    'results': {}
                },
                'api_tests': {
                    'run': False,
                    'success': False,
                    'results': {}
                },
                'validation_tests': {
                    'run': False,
                    'success': False,
                    'results': {}
                },
                'ui_tests': {
                    'run': False,
                    'success': False,
                    'results': {}
                }
            },
            'monitoring': {
                'run': False,
                'success': False,
                'results': {}
            },
            'overall': {
                'success': False,
                'issues': []
            }
        }
    
    def run_unit_tests(self):
        """Run unit tests for the dashboard"""
        if not TESTS_AVAILABLE:
            logger.warning("Skipping unit tests: Test modules not available")
            self.results['tests']['unit_tests']['run'] = False
            self.results['overall']['issues'].append("Unit tests skipped: Test modules not available")
            return False
        
        logger.info("Running unit tests...")
        
        try:
            # Create a test suite
            suite = unittest.TestSuite()
            
            # Add test cases
            suite.addTest(unittest.makeSuite(TestDashboardAPI))
            suite.addTest(unittest.makeSuite(TestDashboardDataFunctions))
            suite.addTest(unittest.makeSuite(TestDashboardFileOperations))
            
            # Run the tests
            runner = unittest.TextTestRunner(verbosity=2)
            result = runner.run(suite)
            
            # Store results
            self.results['tests']['unit_tests']['run'] = True
            self.results['tests']['unit_tests']['success'] = result.wasSuccessful()
            self.results['tests']['unit_tests']['results'] = {
                'total': result.testsRun,
                'errors': len(result.errors),
                'failures': len(result.failures),
                'skipped': len(result.skipped) if hasattr(result, 'skipped') else 0
            }
            
            if not result.wasSuccessful():
                for error in result.errors:
                    self.results['overall']['issues'].append(f"Unit test error: {error[0]}")
                for failure in result.failures:
                    self.results['overall']['issues'].append(f"Unit test failure: {failure[0]}")
            
            logger.info(f"Unit tests completed: {result.testsRun} tests, {len(result.failures)} failures, {len(result.errors)} errors")
            return result.wasSuccessful()
        
        except Exception as e:
            logger.error(f"Error running unit tests: {e}")
            self.results['tests']['unit_tests']['run'] = True
            self.results['tests']['unit_tests']['success'] = False
            self.results['tests']['unit_tests']['results'] = {
                'error': str(e)
            }
            self.results['overall']['issues'].append(f"Unit tests error: {str(e)}")
            return False
    
    def run_api_tests(self):
        """Run API tests for the dashboard"""
        logger.info("Running API tests...")
        
        endpoints = [
            '/',
            '/api/data',
            '/api/logs',
            '/api/platforms',
            '/api/ml/predictions',
            '/api/performance'
        ]
        
        api_results = {
            'total': len(endpoints),
            'success': 0,
            'failure': 0,
            'endpoints': {}
        }
        
        try:
            for endpoint in endpoints:
                endpoint_result = {
                    'url': f"{self.dashboard_url}{endpoint}",
                    'success': False,
                    'status_code': None,
                    'response_time': None,
                    'error': None
                }
                
                try:
                    start_time = time.time()
                    response = requests.get(f"{self.dashboard_url}{endpoint}", timeout=10)
                    response_time = time.time() - start_time
                    
                    endpoint_result['status_code'] = response.status_code
                    endpoint_result['response_time'] = response_time
                    endpoint_result['success'] = 200 <= response.status_code < 300
                    
                    if endpoint_result['success']:
                        api_results['success'] += 1
                    else:
                        api_results['failure'] += 1
                        self.results['overall']['issues'].append(f"API test failure: {endpoint} returned status code {response.status_code}")
                
                except Exception as e:
                    endpoint_result['error'] = str(e)
                    api_results['failure'] += 1
                    self.results['overall']['issues'].append(f"API test error: {endpoint} - {str(e)}")
                
                api_results['endpoints'][endpoint] = endpoint_result
            
            # Store results
            self.results['tests']['api_tests']['run'] = True
            self.results['tests']['api_tests']['success'] = api_results['failure'] == 0
            self.results['tests']['api_tests']['results'] = api_results
            
            logger.info(f"API tests completed: {api_results['success']} successful, {api_results['failure']} failed")
            return api_results['failure'] == 0
        
        except Exception as e:
            logger.error(f"Error running API tests: {e}")
            self.results['tests']['api_tests']['run'] = True
            self.results['tests']['api_tests']['success'] = False
            self.results['tests']['api_tests']['results'] = {
                'error': str(e)
            }
            self.results['overall']['issues'].append(f"API tests error: {str(e)}")
            return False
    
    def run_validation_tests(self):
        """Run validation tests for the dashboard data"""
        if not VALIDATION_ENABLED:
            logger.warning("Skipping validation tests: Validation utilities not available")
            self.results['tests']['validation_tests']['run'] = False
            self.results['overall']['issues'].append("Validation tests skipped: Validation utilities not available")
            return False
        
        logger.info("Running validation tests...")
        
        validation_results = {
            'total': 0,
            'success': 0,
            'failure': 0,
            'endpoints': {}
        }
        
        try:
            # Test endpoints that return data
            endpoints = [
                '/api/data',
                '/api/logs',
                '/api/platforms',
                '/api/ml/predictions',
                '/api/performance'
            ]
            
            validation_results['total'] = len(endpoints)
            
            for endpoint in endpoints:
                endpoint_result = {
                    'url': f"{self.dashboard_url}{endpoint}",
                    'success': False,
                    'validation_errors': [],
                    'error': None
                }
                
                try:
                    response = requests.get(f"{self.dashboard_url}{endpoint}", timeout=10)
                    
                    if 200 <= response.status_code < 300:
                        data = response.json()
                        
                        # Validate the response data
                        validation_errors = validate_api_response(endpoint, data)
                        
                        endpoint_result['success'] = len(validation_errors) == 0
                        endpoint_result['validation_errors'] = validation_errors
                        
                        if endpoint_result['success']:
                            validation_results['success'] += 1
                        else:
                            validation_results['failure'] += 1
                            for error in endpoint_result['validation_errors']:
                                self.results['overall']['issues'].append(f"Validation error for {endpoint}: {error}")
                    else:
                        endpoint_result['error'] = f"API returned status code {response.status_code}"
                        validation_results['failure'] += 1
                        self.results['overall']['issues'].append(f"Validation test failure: {endpoint} returned status code {response.status_code}")
                
                except Exception as e:
                    endpoint_result['error'] = str(e)
                    validation_results['failure'] += 1
                    self.results['overall']['issues'].append(f"Validation test error: {endpoint} - {str(e)}")
                
                validation_results['endpoints'][endpoint] = endpoint_result
            
            # Store results
            self.results['tests']['validation_tests']['run'] = True
            self.results['tests']['validation_tests']['success'] = validation_results['failure'] == 0
            self.results['tests']['validation_tests']['results'] = validation_results
            
            logger.info(f"Validation tests completed: {validation_results['success']} successful, {validation_results['failure']} failed")
            return validation_results['failure'] == 0
        
        except Exception as e:
            logger.error(f"Error running validation tests: {e}")
            self.results['tests']['validation_tests']['run'] = True
            self.results['tests']['validation_tests']['success'] = False
            self.results['tests']['validation_tests']['results'] = {
                'error': str(e)
            }
            self.results['overall']['issues'].append(f"Validation tests error: {str(e)}")
            return False
    
    def run_ui_tests(self):
        """Run UI tests for the dashboard"""
        logger.info("Running UI tests...")
        
        ui_results = {
            'total': 0,
            'success': 0,
            'failure': 0,
            'components': {}
        }
        
        try:
            # Test UI components
            components = [
                {'name': 'Main page', 'url': '/'},
                {'name': 'Logs page', 'url': '/logs'},
                {'name': 'Accounts page', 'url': '/accounts'},
                {'name': 'Static JS', 'url': '/static/js/dashboard.js'},
                {'name': 'Static CSS', 'url': '/static/css/styles.css'}
            ]
            
            ui_results['total'] = len(components)
            
            for component in components:
                component_result = {
                    'name': component['name'],
                    'url': f"{self.dashboard_url}{component['url']}",
                    'success': False,
                    'status_code': None,
                    'response_time': None,
                    'error': None
                }
                
                try:
                    start_time = time.time()
                    response = requests.get(f"{self.dashboard_url}{component['url']}", timeout=10)
                    response_time = time.time() - start_time
                    
                    component_result['status_code'] = response.status_code
                    component_result['response_time'] = response_time
                    component_result['success'] = 200 <= response.status_code < 300
                    
                    if component_result['success']:
                        ui_results['success'] += 1
                    else:
                        ui_results['failure'] += 1
                        self.results['overall']['issues'].append(f"UI test failure: {component['name']} returned status code {response.status_code}")
                
                except Exception as e:
                    component_result['error'] = str(e)
                    ui_results['failure'] += 1
                    self.results['overall']['issues'].append(f"UI test error: {component['name']} - {str(e)}")
                
                ui_results['components'][component['name']] = component_result
            
            # Store results
            self.results['tests']['ui_tests']['run'] = True
            self.results['tests']['ui_tests']['success'] = ui_results['failure'] == 0
            self.results['tests']['ui_tests']['results'] = ui_results
            
            logger.info(f"UI tests completed: {ui_results['success']} successful, {ui_results['failure']} failed")
            return ui_results['failure'] == 0
        
        except Exception as e:
            logger.error(f"Error running UI tests: {e}")
            self.results['tests']['ui_tests']['run'] = True
            self.results['tests']['ui_tests']['success'] = False
            self.results['tests']['ui_tests']['results'] = {
                'error': str(e)
            }
            self.results['overall']['issues'].append(f"UI tests error: {str(e)}")
            return False
    
    def run_monitoring(self, duration=60):
        """
        Run monitoring for the dashboard
        
        Args:
            duration: Duration to monitor in seconds
        """
        if not MONITORING_ENABLED:
            logger.warning("Skipping monitoring: Monitoring utilities not available")
            self.results['monitoring']['run'] = False
            self.results['overall']['issues'].append("Monitoring skipped: Monitoring utilities not available")
            return False
        
        logger.info(f"Running monitoring for {duration} seconds...")
        
        try:
            # Create and start the monitor
            monitor = DashboardMonitor(dashboard_url=self.dashboard_url)
            monitor.start()
            
            # Monitor for the specified duration
            time.sleep(duration)
            
            # Get monitoring results
            monitoring_results = monitor.get_metrics_summary()
            
            # Stop the monitor
            monitor.stop()
            
            # Store results
            self.results['monitoring']['run'] = True
            self.results['monitoring']['success'] = monitoring_results['success_rate'] >= 90  # Success if at least 90% of checks passed
            self.results['monitoring']['results'] = monitoring_results
            
            if not self.results['monitoring']['success']:
                self.results['overall']['issues'].append(f"Monitoring failure: Success rate {monitoring_results['success_rate']:.2f}% is below 90%")
            
            logger.info(f"Monitoring completed: Success rate {monitoring_results['success_rate']:.2f}%")
            return self.results['monitoring']['success']
        
        except Exception as e:
            logger.error(f"Error running monitoring: {e}")
            self.results['monitoring']['run'] = True
            self.results['monitoring']['success'] = False
            self.results['monitoring']['results'] = {
                'error': str(e)
            }
            self.results['overall']['issues'].append(f"Monitoring error: {str(e)}")
            return False
    
    def run_all_tests(self, monitoring_duration=60):
        """
        Run all tests and monitoring
        
        Args:
            monitoring_duration: Duration to monitor in seconds
        
        Returns:
            True if all tests passed, False otherwise
        """
        logger.info("Running all tests...")
        
        # Run tests
        unit_tests_success = self.run_unit_tests()
        api_tests_success = self.run_api_tests()
        validation_tests_success = self.run_validation_tests()
        ui_tests_success = self.run_ui_tests()
        
        # Run monitoring
        monitoring_success = self.run_monitoring(duration=monitoring_duration)
        
        # Calculate overall success
        self.results['overall']['success'] = (
            (unit_tests_success or not TESTS_AVAILABLE) and
            api_tests_success and
            (validation_tests_success or not VALIDATION_ENABLED) and
            ui_tests_success and
            (monitoring_success or not MONITORING_ENABLED)
        )
        
        return self.results['overall']['success']
    
    def generate_report(self, output_file=None):
        """
        Generate a report of the test results
        
        Args:
            output_file: Path to the output file, or None to print to console
        
        Returns:
            The report as a string
        """
        # Calculate overall status
        status = "PASSED" if self.results['overall']['success'] else "FAILED"
        
        # Generate report
        report = f"""
=======================================================
KryptoBot Dashboard Test Report
=======================================================
Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Dashboard URL: {self.dashboard_url}
Overall Status: {status}

-------------------------------------------------------
Test Results
-------------------------------------------------------
"""
        
        # Unit tests
        if self.results['tests']['unit_tests']['run']:
            unit_tests_status = "PASSED" if self.results['tests']['unit_tests']['success'] else "FAILED"
            unit_tests_results = self.results['tests']['unit_tests']['results']
            
            report += f"""
Unit Tests: {unit_tests_status}
- Total tests: {unit_tests_results.get('total', 'N/A')}
- Errors: {unit_tests_results.get('errors', 'N/A')}
- Failures: {unit_tests_results.get('failures', 'N/A')}
- Skipped: {unit_tests_results.get('skipped', 'N/A')}
"""
        else:
            report += "\nUnit Tests: SKIPPED\n"
        
        # API tests
        if self.results['tests']['api_tests']['run']:
            api_tests_status = "PASSED" if self.results['tests']['api_tests']['success'] else "FAILED"
            api_tests_results = self.results['tests']['api_tests']['results']
            
            report += f"""
API Tests: {api_tests_status}
- Total endpoints: {api_tests_results.get('total', 'N/A')}
- Successful: {api_tests_results.get('success', 'N/A')}
- Failed: {api_tests_results.get('failure', 'N/A')}

Endpoint Details:
"""
            
            for endpoint, result in api_tests_results.get('endpoints', {}).items():
                endpoint_status = "PASSED" if result.get('success', False) else "FAILED"
                report += f"- {endpoint}: {endpoint_status} (Status: {result.get('status_code', 'N/A')}, Time: {result.get('response_time', 'N/A'):.3f}s)\n"
                if result.get('error'):
                    report += f"  Error: {result['error']}\n"
        else:
            report += "\nAPI Tests: SKIPPED\n"
        
        # Validation tests
        if self.results['tests']['validation_tests']['run']:
            validation_tests_status = "PASSED" if self.results['tests']['validation_tests']['success'] else "FAILED"
            validation_tests_results = self.results['tests']['validation_tests']['results']
            
            report += f"""
Validation Tests: {validation_tests_status}
- Total endpoints: {validation_tests_results.get('total', 'N/A')}
- Successful: {validation_tests_results.get('success', 'N/A')}
- Failed: {validation_tests_results.get('failure', 'N/A')}

Endpoint Details:
"""
            
            for endpoint, result in validation_tests_results.get('endpoints', {}).items():
                endpoint_status = "PASSED" if result.get('success', False) else "FAILED"
                report += f"- {endpoint}: {endpoint_status}\n"
                if result.get('error'):
                    report += f"  Error: {result['error']}\n"
                for error in result.get('validation_errors', [])[:5]:  # Show first 5 errors
                    report += f"  Validation Error: {error}\n"
                if len(result.get('validation_errors', [])) > 5:
                    report += f"  ... and {len(result.get('validation_errors', [])) - 5} more errors\n"
        else:
            report += "\nValidation Tests: SKIPPED\n"
        
        # UI tests
        if self.results['tests']['ui_tests']['run']:
            ui_tests_status = "PASSED" if self.results['tests']['ui_tests']['success'] else "FAILED"
            ui_tests_results = self.results['tests']['ui_tests']['results']
            
            report += f"""
UI Tests: {ui_tests_status}
- Total components: {ui_tests_results.get('total', 'N/A')}
- Successful: {ui_tests_results.get('success', 'N/A')}
- Failed: {ui_tests_results.get('failure', 'N/A')}

Component Details:
"""
            
            for component, result in ui_tests_results.get('components', {}).items():
                component_status = "PASSED" if result.get('success', False) else "FAILED"
                report += f"- {component}: {component_status} (Status: {result.get('status_code', 'N/A')}, Time: {result.get('response_time', 'N/A'):.3f}s)\n"
                if result.get('error'):
                    report += f"  Error: {result['error']}\n"
        else:
            report += "\nUI Tests: SKIPPED\n"
        
        # Monitoring
        if self.results['monitoring']['run']:
            monitoring_status = "PASSED" if self.results['monitoring']['success'] else "FAILED"
            monitoring_results = self.results['monitoring']['results']
            
            report += f"""
Monitoring: {monitoring_status}
- Uptime: {monitoring_results.get('uptime_formatted', 'N/A')}
- Success rate: {monitoring_results.get('success_rate', 'N/A'):.2f}%
- Average response time: {monitoring_results.get('avg_response_time', 'N/A'):.3f}s
- Total checks: {monitoring_results.get('total_checks', 'N/A')}
- Successful checks: {monitoring_results.get('successful_checks', 'N/A')}
- Failed checks: {monitoring_results.get('failed_checks', 'N/A')}
"""
            
            if monitoring_results.get('recent_alerts'):
                report += "\nRecent Alerts:\n"
                for alert in monitoring_results.get('recent_alerts', []):
                    report += f"- {alert.get('timestamp', 'N/A')}: {alert.get('message', 'N/A')}\n"
        else:
            report += "\nMonitoring: SKIPPED\n"
        
        # Issues
        if self.results['overall']['issues']:
            report += "\n-------------------------------------------------------\nIssues\n-------------------------------------------------------\n"
            for issue in self.results['overall']['issues']:
                report += f"- {issue}\n"
        
        # Conclusion
        report += f"""
-------------------------------------------------------
Conclusion
-------------------------------------------------------
The dashboard is {"operational" if self.results['overall']['success'] else "not operational"}.
"""
        
        # Write report to file if specified
        if output_file:
            try:
                os.makedirs(os.path.dirname(output_file), exist_ok=True)
                with open(output_file, 'w') as f:
                    f.write(report)
                logger.info(f"Report written to {output_file}")
            except Exception as e:
                logger.error(f"Error writing report to {output_file}: {e}")
        
        return report

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Run dashboard tests and monitoring')
    parser.add_argument('--url', default='http://localhost:5001', help='Dashboard URL')
    parser.add_argument('--output', default='reports/dashboard_test_report.txt', help='Output file for the report')
    parser.add_argument('--monitoring-duration', type=int, default=60, help='Duration to monitor in seconds')
    parser.add_argument('--json-output', default='reports/dashboard_test_results.json', help='JSON output file for the results')
    args = parser.parse_args()
    
    # Create directories
    os.makedirs('logs', exist_ok=True)
    os.makedirs('reports', exist_ok=True)
    
    # Run tests
    runner = DashboardTestRunner(dashboard_url=args.url)
    success = runner.run_all_tests(monitoring_duration=args.monitoring_duration)
    
    # Generate report
    report = runner.generate_report(output_file=args.output)
    print(report)
    
    # Save results as JSON
    try:
        with open(args.json_output, 'w') as f:
            json.dump(runner.results, f, indent=2)
        logger.info(f"Results written to {args.json_output}")
    except Exception as e:
        logger.error(f"Error writing results to {args.json_output}: {e}")
    
    # Return success status
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main()) 