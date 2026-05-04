import yaml
from pathlib import Path
import os

CONFIG_PATH = "/var/lib/bandwidth-guard/config.yaml"
os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)


def load_enforcement_config():
    #Load process limit configuration from YAML 
    try:
        with open(CONFIG_PATH, 'r') as f:
            config = yaml.safe_load(f)
        return config or {}
    except FileNotFoundError:
        return {
            'global': {},
            'processes': {},
            'whitelist': ['sshd', 'systemd']
        }

def save_limit_config(config):
    #Save config back to YAML   
    
    with open(CONFIG_PATH, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)


def get_data_plan():
    #Get user's data plan
    config = load_enforcement_config()
    return config.get('global', {}).get('data_plan', 'Not configured')

def set_data_plan(plan_name, limit_mb):
    #Set user's data plan
    config = load_enforcement_config()
    
    if 'global' not in config:
        config['global'] = {}
    
    config['global']['data_plan'] = plan_name
    config['global']['daily_limit_mb'] = limit_mb
    
    save_limit_config(config)