import json
import os
from unittest import mock
import pytest

from candidate_transformer.export.json_server import JsonServerManager, PID_FILE, DB_FILE, RUNTIME_DIR

@pytest.fixture(autouse=True)
def clean_runtime():
    if PID_FILE.exists():
        PID_FILE.unlink()
    if DB_FILE.exists():
        DB_FILE.unlink()
    yield
    if PID_FILE.exists():
        PID_FILE.unlink()
    if DB_FILE.exists():
        DB_FILE.unlink()

@mock.patch("shutil.which")
@mock.patch("subprocess.Popen")
@mock.patch("candidate_transformer.export.json_server.JsonServerManager._is_process_alive")
def test_server_lifecycle(mock_is_alive, mock_popen, mock_which):
    mock_which.return_value = "/usr/bin/json-server"
    
    # Ensure runtime dir exists and fake a DB file
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    DB_FILE.touch()
    
    # Mock Popen
    mock_process = mock.Mock()
    mock_process.pid = 9999
    mock_popen.return_value = mock_process
    
    # 1. Start Server
    mock_is_alive.return_value = True
    result = JsonServerManager.start("test_workspace")
    
    assert result["status"] == "Running"
    assert result["pid"] == 9999
    assert result["workspace"] == "test_workspace"
    assert PID_FILE.exists()
    
    with open(PID_FILE) as f:
        meta = json.load(f)
        assert meta["pid"] == 9999
        assert meta["workspace"] == "test_workspace"
        
    # 2. Duplicate Launch Prevention
    # It should read status as Running, and return early
    result2 = JsonServerManager.start("test_workspace")
    assert mock_popen.call_count == 1  # Verify Popen not called again
    assert result2["status"] == "Running"
    
    # 3. Server Stop
    # Mock os.kill to avoid actually killing arbitrary PIDs during test if not mocked
    with mock.patch("os.kill") as mock_kill, mock.patch("subprocess.run") as mock_run:
        stopped = JsonServerManager.stop()
        assert stopped is True
        assert not PID_FILE.exists()
