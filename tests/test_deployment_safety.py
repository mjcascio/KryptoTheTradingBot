"""Tests for the deployment safety module."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.utils.deployment_safety import DeploymentSafety


@pytest.fixture
def temp_project_dir(tmp_path):
    """Create a temporary project directory for testing."""
    return str(tmp_path / "test_project")


@pytest.fixture
def deployment_safety(temp_project_dir):
    """Create a DeploymentSafety instance for testing."""
    return DeploymentSafety(temp_project_dir)


def test_init_creates_directories(deployment_safety, temp_project_dir):
    """Test that initialization creates necessary directories."""
    project_root = Path(temp_project_dir)
    
    assert (project_root / 'backups').exists()
    assert (project_root / 'test_results').exists()
    assert (project_root / 'logs' / 'deployment').exists()


@patch('subprocess.run')
def test_create_backup_success(mock_run, deployment_safety):
    """Test successful backup creation."""
    mock_run.return_value = MagicMock(returncode=0)
    
    backup_branch = deployment_safety.create_backup()
    
    assert backup_branch.startswith('backup/')
    assert mock_run.call_count == 3  # checkout, add, commit


@patch('subprocess.run')
def test_create_backup_failure(mock_run, deployment_safety):
    """Test backup creation failure."""
    mock_run.side_effect = Exception("Git error")
    
    with pytest.raises(RuntimeError):
        deployment_safety.create_backup()


@patch('subprocess.run')
def test_run_tests_all_pass(mock_run, deployment_safety):
    """Test when all tests pass."""
    mock_run.return_value = MagicMock(
        returncode=0,
        stdout="All tests passed"
    )
    
    assert deployment_safety.run_tests() is True


@patch('subprocess.run')
def test_run_tests_failure(mock_run, deployment_safety):
    """Test when tests fail."""
    mock_run.return_value = MagicMock(
        returncode=1,
        stdout="Test failures occurred"
    )
    
    assert deployment_safety.run_tests() is False


@patch('subprocess.run')
def test_rollback_changes_success(mock_run, deployment_safety):
    """Test successful rollback."""
    mock_run.return_value = MagicMock(returncode=0)
    
    assert deployment_safety.rollback_changes('backup/test') is True
    assert mock_run.call_count == 2  # stash and checkout


@patch('subprocess.run')
def test_rollback_changes_failure(mock_run, deployment_safety):
    """Test rollback failure."""
    mock_run.side_effect = Exception("Git error")
    
    assert deployment_safety.rollback_changes('backup/test') is False


def test_verify_system_health(deployment_safety):
    """Test system health verification."""
    health_status = deployment_safety.verify_system_health()
    
    assert isinstance(health_status, dict)
    assert all(isinstance(v, bool) for v in health_status.values())
    assert 'trading_engine' in health_status
    assert 'monitoring' in health_status
    assert 'remote_control' in health_status
    assert 'data_feeds' in health_status


@patch('builtins.open')
@patch('subprocess.run')
def test_update_documentation(mock_run, mock_open, deployment_safety):
    """Test documentation update."""
    changes = ['Change 1', 'Change 2']
    mock_file = MagicMock()
    mock_open.return_value.__enter__.return_value = mock_file
    
    deployment_safety.update_documentation(changes)
    
    mock_file.write.assert_called()
    assert mock_run.call_count == 2  # add and commit 