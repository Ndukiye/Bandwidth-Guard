from unittest.mock import Mock, patch, MagicMock
from src.monitor import normalize_bpftrace_line, get_process_owner, increment_process_data
import psutil

class TestNormalizeBpftraceLine:
    """Test bpftrace output parsing"""
    
    def test_parse_valid_send_line(self, mocker):
        """Test parsing a valid @send_bytes line"""
        mock_line = '@send_bytes[60852, Chrome_ChildIOT]: 1048576'
        
        # Mock get_process_owner to return parent process
        mocker.patch('src.monitor.get_process_owner', return_value='chrome')
        
        # Mock psutil.Process (it won't be called since get_process_owner returns a value)
        mock_process = MagicMock()
        mock_process.name.return_value = 'Chrome_ChildIOT'
        mocker.patch('src.monitor.psutil.Process', return_value=mock_process)
        
        result = normalize_bpftrace_line(mock_line)
        
        assert result == {"megabytes": 1.0, "name": "chrome"}
    
    
    def test_parse_valid_recv_line(self, mocker):
        """Test parsing a valid @recv_bytes line"""
        mock_line = '@recv_bytes[12345, firefox]: 524288'  # 0.5 MB
        
        mocker.patch('src.monitor.get_process_owner', return_value=None)
        
        mock_process = MagicMock()
        mock_process.name.return_value = 'firefox'
        mocker.patch('src.monitor.psutil.Process', return_value=mock_process)
        
        result = normalize_bpftrace_line(mock_line)
        
        assert result == {"megabytes": 0.5, "name": "firefox"}
    
    
    def test_parse_uses_process_owner_when_available(self, mocker):
        """Test that parent process name is used when available"""
        mock_line = '@send_bytes[60852, Helper]: 1048576'
        
        # Child process should be bundled under parent
        mocker.patch('src.monitor.get_process_owner', return_value='spotify')
        
        result = normalize_bpftrace_line(mock_line)
        
        assert result['name'] == 'spotify'  # Uses parent, not 'Helper'
    
    
    def test_parse_uses_psutil_name_when_no_owner(self, mocker):
        """Test that psutil Process.name() is used when no parent found"""
        mock_line = '@send_bytes[12345, systemd]: 1048576'
        
        # No parent process (standalone process)
        mocker.patch('src.monitor.get_process_owner', return_value=None)
        
        mock_process = MagicMock()
        mock_process.name.return_value = 'systemd'
        mocker.patch('src.monitor.psutil.Process', return_value=mock_process)
        
        result = normalize_bpftrace_line(mock_line)
        
        assert result['name'] == 'systemd'
    
    
    def test_parse_uses_comm_name_when_process_not_found(self, mocker):
        """Test fallback to comm name when psutil fails"""
        mock_line = '@send_bytes[99999, ghost_process]: 1048576'
        
        mocker.patch('src.monitor.get_process_owner', return_value=None)
        
        # Process no longer exists
        mocker.patch('src.monitor.psutil.Process', side_effect=psutil.NoSuchProcess(99999))
        
        result = normalize_bpftrace_line(mock_line)
        
        assert result['name'] == 'ghost_process'  # Falls back to comm name
    
    
    def test_parse_handles_access_denied(self, mocker):
        """Test fallback when permission denied on process"""
        mock_line = '@send_bytes[1, root_process]: 1048576'
        
        mocker.patch('src.monitor.get_process_owner', return_value=None)
        mocker.patch('src.monitor.psutil.Process', side_effect=psutil.AccessDenied(1))
        
        result = normalize_bpftrace_line(mock_line)
        
        assert result['name'] == 'root_process'
    
    
    def test_parse_different_byte_sizes(self, mocker):
        """Test parsing different byte values"""
        mocker.patch('src.monitor.get_process_owner', return_value=None)
        mock_process = MagicMock()
        mock_process.name.return_value = 'test'
        mocker.patch('src.monitor.psutil.Process', return_value=mock_process)
        
        test_cases = [
            ('@send_bytes[1, test]: 0', 0.0),           # 0 bytes
            ('@send_bytes[1, test]: 1024', 1024 / (1024 * 1024)),  # 1 KB
            ('@send_bytes[1, test]: 1048576', 1.0),     # 1 MB
            ('@send_bytes[1, test]: 10485760', 10.0),   # 10 MB
            ('@send_bytes[1, test]: 104857600', 100.0), # 100 MB
        ]
        
        for line, expected_mb in test_cases:
            result = normalize_bpftrace_line(line)
            assert result['megabytes'] == expected_mb
    
    
    def test_parse_extracts_correct_pid(self, mocker):
        """Test that PID is correctly extracted and passed to psutil"""
        mock_line = '@send_bytes[42, process_name]: 1048576'
        
        mocker.patch('src.monitor.get_process_owner', return_value=None)
        
        mock_process_class = mocker.patch('src.monitor.psutil.Process')
        mock_process = MagicMock()
        mock_process.name.return_value = 'test'
        mock_process_class.return_value = mock_process
        
        normalize_bpftrace_line(mock_line)
        
        # Verify psutil.Process was called with correct PID
        mock_process_class.assert_called_once_with(42)
    
    
    def test_parse_malformed_line_returns_none(self, mocker):
        """Test that malformed input returns None gracefully"""
        # Note: Your current implementation doesn't handle this!
        # This test will fail until you add error handling
        
        malformed_lines = [
            'garbage data',
            '@send_bytes[]: 1048576',
            '@send_bytes[abc, def]: xyz',
            '',
            None,
        ]
        
        for line in malformed_lines:
            result = normalize_bpftrace_line(line)
            assert result is None, f"Should return None for: {line}"


class TestGetProcessOwner:
    """Test process parent detection for bundling children"""
    
    def test_returns_firefox_for_firefox_child(self, mocker):
        """Test that Firefox child processes are bundled under 'firefox'"""
        # Mock process tree: firefox (PID 1000) -> firefox-child (PID 2000)
        
        mock_child = MagicMock()
        mock_child.pid = 2000
        
        mock_firefox = MagicMock()
        mock_firefox.info = {'pid': 1000, 'name': 'firefox'}
        mock_firefox.children.return_value = [mock_child]
        
        mock_other_process = MagicMock()
        mock_other_process.info = {'pid': 500, 'name': 'systemd'}
        
        mocker.patch('src.monitor.psutil.process_iter', return_value=[
            mock_other_process,
            mock_firefox
        ])
        
        result = get_process_owner(2000)
        
        assert result == 'firefox'
    
    
    def test_returns_chrome_for_chrome_helper(self, mocker):
        """Test that Chrome helper processes are bundled under 'chrome'"""
        mock_helper = MagicMock()
        mock_helper.pid = 3000
        
        mock_chrome = MagicMock()
        mock_chrome.info = {'pid': 2000, 'name': 'chrome'}
        mock_chrome.children.return_value = [mock_helper]
        
        mocker.patch('src.monitor.psutil.process_iter', return_value=[mock_chrome])
        
        result = get_process_owner(3000)
        
        assert result == 'chrome'
    
    
    def test_returns_none_for_standalone_process(self, mocker):
        """Test that processes without major app parents return None"""
        mock_firefox = MagicMock()
        mock_firefox.info = {'pid': 1000, 'name': 'firefox'}
        mock_firefox.children.return_value = []  # No children
        
        mocker.patch('src.monitor.psutil.process_iter', return_value=[mock_firefox])
        
        # PID 5000 is not a child of any major app
        result = get_process_owner(5000)
        
        assert result is None
    
    
    def test_returns_none_for_non_major_app_parent(self, mocker):
        """Test that children of non-major apps return None"""
        # systemd is not in MAJOR_APPS
        mock_child = MagicMock()
        mock_child.pid = 2000
        
        mock_systemd = MagicMock()
        mock_systemd.info = {'pid': 1, 'name': 'systemd'}
        mock_systemd.children.return_value = [mock_child]
        
        mocker.patch('src.monitor.psutil.process_iter', return_value=[mock_systemd])
        
        result = get_process_owner(2000)
        
        assert result is None
    
    
    def test_handles_process_access_denied(self, mocker):
        """Test graceful handling when access denied on process"""
        mock_process = MagicMock()
        mock_process.info = {'pid': 1000, 'name': 'firefox'}
        mock_process.children.side_effect = psutil.AccessDenied(1000)
        
        mocker.patch('src.monitor.psutil.process_iter', return_value=[mock_process])
        
        result = get_process_owner(2000)
        
        # Should not crash, should return None
        assert result is None
    
    
    def test_handles_process_no_longer_exists(self, mocker):
        """Test graceful handling when process dies during iteration"""
        mock_process = MagicMock()
        mock_process.info = {'pid': 1000, 'name': 'firefox'}
        mock_process.children.side_effect = psutil.NoSuchProcess(1000)
        
        mocker.patch('src.monitor.psutil.process_iter', return_value=[mock_process])
        
        result = get_process_owner(2000)
        
        assert result is None
    
    
    def test_only_checks_major_apps(self, mocker):
        """Test that only processes in MAJOR_APPS are checked"""
        # MAJOR_APPS = {'firefox', 'chrome', 'spotify', 'code', 'teams'}
        
        mock_child = MagicMock()
        mock_child.pid = 2000
        
        mock_vscode = MagicMock()
        mock_vscode.info = {'pid': 1000, 'name': 'code'}  # In MAJOR_APPS
        mock_vscode.children.return_value = [mock_child]
        
        mock_python = MagicMock()
        mock_python.info = {'pid': 500, 'name': 'python'}  # Not in MAJOR_APPS
        mock_python.children.return_value = [mock_child]
        
        mocker.patch('src.monitor.psutil.process_iter', return_value=[
            mock_python,  # Should be skipped
            mock_vscode   # Should be checked
        ])
        
        result = get_process_owner(2000)
        
        # Should return 'code', not 'python'
        assert result == 'code'
    
    
    def test_returns_parent_when_pid_matches_parent(self, mocker):
        """Test that parent PID itself returns the parent name"""
        mock_firefox = MagicMock()
        mock_firefox.info = {'pid': 1000, 'name': 'firefox'}
        mock_firefox.pid = 1000
        mock_firefox.children.return_value = []
        
        mocker.patch('src.monitor.psutil.process_iter', return_value=[mock_firefox])
        
        # Check if PID 1000 (the parent itself) returns 'firefox'
        result = get_process_owner(1000)
        
        assert result == 'firefox'

class TestIncrementProcessData:
    """Test process usage tracking and storage"""
    
    def test_increments_send_data(self, mocker):
        """Test incrementing send bytes for a process"""
        # Start with empty state
        from src.monitor import proc_nd_usage
        proc_nd_usage.clear()
        
        mock_update = mocker.patch('src.monitor.update_today_usage')
        
        increment_process_data('firefox', 10.5, 'send')
        
        # Check in-memory state
        assert proc_nd_usage['firefox']['send'] == 10.5
        assert proc_nd_usage['firefox']['recv'] == 0
        
        # Check persistence call
        mock_update.assert_called_once_with('firefox', 10.5, 0)
    
    
    def test_increments_recv_data(self, mocker):
        """Test incrementing recv bytes for a process"""
        from src.monitor import proc_nd_usage
        proc_nd_usage.clear()
        
        mock_update = mocker.patch('src.monitor.update_today_usage')
        
        increment_process_data('chrome', 25.3, 'recv')
        
        assert proc_nd_usage['chrome']['send'] == 0
        assert proc_nd_usage['chrome']['recv'] == 25.3
        
        mock_update.assert_called_once_with('chrome', 0, 25.3)
    
    
    def test_accumulates_multiple_increments(self, mocker):
        """Test that multiple increments accumulate correctly"""
        from src.monitor import proc_nd_usage
        proc_nd_usage.clear()
        
        mock_update = mocker.patch('src.monitor.update_today_usage')
        
        increment_process_data('firefox', 10.0, 'send')
        increment_process_data('firefox', 5.0, 'send')
        increment_process_data('firefox', 20.0, 'recv')
        
        assert proc_nd_usage['firefox']['send'] == 15.0
        assert proc_nd_usage['firefox']['recv'] == 20.0
        
        # Should have called update_today_usage 3 times
        assert mock_update.call_count == 3
        
        # Last call should have accumulated values
        mock_update.assert_called_with('firefox', 15.0, 20.0)
    
    
    def test_tracks_multiple_processes(self, mocker):
        """Test tracking multiple processes independently"""
        from src.monitor import proc_nd_usage
        proc_nd_usage.clear()
        
        mock_update = mocker.patch('src.monitor.update_today_usage')
        
        increment_process_data('firefox', 10.0, 'send')
        increment_process_data('chrome', 20.0, 'recv')
        increment_process_data('spotify', 5.0, 'send')
        
        assert proc_nd_usage['firefox']['send'] == 10.0
        assert proc_nd_usage['chrome']['recv'] == 20.0
        assert proc_nd_usage['spotify']['send'] == 5.0
        
        # Each process should have been persisted
        assert mock_update.call_count == 3
    
    
    def test_persists_to_storage_every_call(self, mocker):
        """Test that every increment triggers storage update"""
        from src.monitor import proc_nd_usage
        proc_nd_usage.clear()
        
        mock_update = mocker.patch('src.monitor.update_today_usage')
        
        increment_process_data('firefox', 1.0, 'send')
        increment_process_data('firefox', 1.0, 'send')
        increment_process_data('firefox', 1.0, 'send')
        
        # Should have called update 3 times (once per increment)
        assert mock_update.call_count == 3
    
    
    def test_handles_zero_bytes(self, mocker):
        """Test incrementing with 0 bytes (edge case)"""
        from src.monitor import proc_nd_usage
        proc_nd_usage.clear()
        
        mock_update = mocker.patch('src.monitor.update_today_usage')
        
        increment_process_data('firefox', 0, 'send')
        
        assert proc_nd_usage['firefox']['send'] == 0
        mock_update.assert_called_once_with('firefox', 0, 0)
    
    
    def test_handles_large_values(self, mocker):
        """Test incrementing with large byte values"""
        from src.monitor import proc_nd_usage
        proc_nd_usage.clear()
        
        mock_update = mocker.patch('src.monitor.update_today_usage')
        
        # 1000 MB
        increment_process_data('firefox', 1000.0, 'send')
        
        assert proc_nd_usage['firefox']['send'] == 1000.0
        mock_update.assert_called_once_with('firefox', 1000.0, 0)