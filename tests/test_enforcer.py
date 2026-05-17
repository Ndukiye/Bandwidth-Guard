import time
from unittest.mock import Mock, patch
from src.enforcer import enforce_limit, should_notify, check_cap

def test_enforce_limit(mocker):
    mocker.patch('src.enforcer.get_pids_by_name', return_value=[1234]) ##Mock Pids
    mock_notify = mocker.patch('src.enforcer.notify_user')
    mock_kill = mocker.patch('src.enforcer.kill_process')

    enforce_limit('firefox', 200, 200, action='kill')
    mock_kill.assert_called_once_with([1234])
    assert 'Killed firefox' in mock_notify.call_args[0][0]

def test_should_notify_notification_cooldown():
    #first notification should run successfully
    assert should_notify("firefox", 'warn_80') == True

    #second immediate notification should fail because of cooldown
    assert should_notify("firefox", 'warn_80') == False

    with patch('time.time', return_value=time.time()+181):
        assert should_notify("firefox", 'warn_80') == True

def test_check_cap_global(mocker):
    # should return False cause global limit isnt set
    mocker.patch('src.enforcer.load_enforcement_config',return_value={})
    assert check_cap(300) == False

    # Test 2 & 3: With limit
    mock_config = mocker.patch('src.enforcer.load_enforcement_config', return_value={
            'global': {'daily_limit_mb': 250, 'data_plan': '300'}
        })
    assert check_cap(200) == False # Below Limit
    assert check_cap(251) == True   # Above Limit

    