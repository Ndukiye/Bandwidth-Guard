# src/config_loader.py
import yaml
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def load_enforcement_config():
    """Load process limit configuration from YAML"""
    config_path = BASE_DIR / "config.yaml"
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        # Return default config if file doesn't exist
        return {
            'global': {'daily_limit_mb': 5120},
            'processes': {},
            'whitelist': ['sshd', 'systemd']
        }