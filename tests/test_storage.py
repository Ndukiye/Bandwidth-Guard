from unittest.mock import Mock, patch
from src.storage import update_today_usage,get_date_range_usage,cleanup_old_history
from datetime import date
def test_update_today_storage(mocker):
    mock_save = mocker.patch('src.storage.save_history')
    mocker.patch('src.storage.load_history', return_value={
    "2026-05-16": {
        "code": {
            "send": 60,
            "recv": 600,
            "total": 660
        },
        "spotify": {
            "send": 2,
            "recv": 500,
            "total": 502
        }}})
    mocker.patch('src.storage.get_today_str',return_value='2026-05-16')

    update_today_usage('code',100,100)
    mock_save.assert_called_once_with({    
        "2026-05-16": {
        "code": {
            "send": 100,
            "recv": 100,
            "total": 200
        },
        "spotify": {
            "send": 2,
            "recv": 500,
            "total": 502
        }
        }})

def test_get_date_range_usage(mocker):
    mock_data = {
    "2026-05-16": {
        "code": {
            "send": 60,
            "recv": 600,
            "total": 660
        }
    },
    "2026-05-17": {
        "spotify": {
            "send": 2,
            "recv": 500,
            "total": 502
        }
    }}
    expected_result= {
        "code": {
            "send": 60,
            "recv": 600,
            "total": 660,
        },
        "spotify": {
            "send": 2,
            "recv": 500,
            "total": 502,
        },
    }
    mocker.patch('src.storage.load_history', return_value=mock_data)
    mock_start_date = date(2026, 5, 16)
    mock_end_date = date(2026, 5, 17)
    assert get_date_range_usage(mock_start_date,mock_end_date) == expected_result
    
def test_cleanup_old_history(mocker):
    mock_data = {
    "2026-04-16": {
        "code": {
            "send": 60,
            "recv": 600,
            "total": 660
        }
    },
    "2026-05-17": {
        "spotify": {
            "send": 2,
            "recv": 500,
            "total": 502
        }
    }}
    mocker.patch('src.storage.load_history',return_value=mock_data)
    mock_save_history = mocker.patch('src.storage.save_history')
    cleanup_old_history(1)
    mock_save_history.assert_called_once_with({    
    "2026-05-17": {
        "spotify": {
            "send": 2,
            "recv": 500,
            "total": 502
        }
    }})
    