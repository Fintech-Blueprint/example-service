import os
import json
from datetime import datetime
from pathlib import Path
import pytest
import yaml
from unittest.mock import patch, mock_open

from src.core.mode_manager import ModeTransitionManager

@pytest.fixture
def mode_manager():
    with patch('builtins.open', mock_open(read_data=yaml.dump({
        'org': {
            'resource_limits': {
                'compliance': {
                    'cpu': '0.1-0.5',
                    'memory': '128Mi-512Mi'
                }
            }
        }
    }))):
        return ModeTransitionManager('test-service')

@pytest.fixture
def mock_reports_dir(tmp_path):
    reports_dir = tmp_path / 'services/test-service/reports/latest'
    reports_dir.mkdir(parents=True)
    return reports_dir

def test_validate_compliance_readiness_missing_files(mode_manager):
    """Test validation when required files are missing"""
    results = mode_manager.validate_compliance_readiness()
    assert not all(results.values())
    assert not results['tests_passing']
    assert not results['sast_passing']
    assert not results['signatures_valid']
    assert not results['resource_limits_ok']

def test_validate_compliance_readiness_passing(mode_manager, mock_reports_dir):
    """Test validation when all checks pass"""
    # Create test files
    coverage_data = {'total_coverage': 80}
    with open(mock_reports_dir / 'coverage.json', 'w') as f:
        json.dump(coverage_data, f)
    
    sast_data = {'high_severity_issues': 0}
    with open(mock_reports_dir / 'sast-report.json', 'w') as f:
        json.dump(sast_data, f)
    
    resource_data = {'cpu_usage': 0.3, 'memory_usage': 256}
    with open(mock_reports_dir / 'resource-usage.json', 'w') as f:
        json.dump(resource_data, f)
    
    # Create signature file
    (mock_reports_dir / 'test.sig').touch()
    
    with patch('pathlib.Path') as mock_path:
        mock_path.return_value = mock_reports_dir
        results = mode_manager.validate_compliance_readiness()
        assert all(results.values())

def test_validate_compliance_readiness_failing_tests(mode_manager, mock_reports_dir):
    """Test validation when test coverage is too low"""
    coverage_data = {'total_coverage': 60}  # Below 70% requirement
    with open(mock_reports_dir / 'coverage.json', 'w') as f:
        json.dump(coverage_data, f)
        
    with patch('pathlib.Path') as mock_path:
        mock_path.return_value = mock_reports_dir
        results = mode_manager.validate_compliance_readiness()
        assert not results['tests_passing']

def test_request_compliance_mode_already_compliant():
    """Test requesting compliance mode when already in it"""
    with patch.dict(os.environ, {'SERVICE_MODE': 'compliance'}):
        with patch('builtins.open', mock_open(read_data=yaml.dump({}))):
            manager = ModeTransitionManager('test-service')
            result = manager.request_compliance_mode()
            assert result == "Already in compliance mode"

def test_request_compliance_mode_failing_checks(mode_manager):
    """Test requesting compliance mode with failing checks"""
    result = manager.request_compliance_mode()
    assert "Failed compliance checks" in result
    assert "tests_passing" in result
    assert "sast_passing" in result

def test_request_compliance_mode_success(mode_manager, mock_reports_dir):
    """Test successful compliance mode request"""
    # Set up passing checks
    coverage_data = {'total_coverage': 80}
    with open(mock_reports_dir / 'coverage.json', 'w') as f:
        json.dump(coverage_data, f)
    
    sast_data = {'high_severity_issues': 0}
    with open(mock_reports_dir / 'sast-report.json', 'w') as f:
        json.dump(sast_data, f)
    
    resource_data = {'cpu_usage': 0.3, 'memory_usage': 256}
    with open(mock_reports_dir / 'resource-usage.json', 'w') as f:
        json.dump(resource_data, f)
    
    (mock_reports_dir / 'test.sig').touch()
    
    with patch('pathlib.Path') as mock_path:
        mock_path.side_effect = lambda x: mock_reports_dir if 'reports' in str(x) else Path(x)
        result = mode_manager.request_compliance_mode()
        assert result is None  # Success
        
        # Verify transition request file was created
        transitions_dir = Path('services/test-service/mode-transitions')
        assert len(list(transitions_dir.glob('request_*.json'))) == 1