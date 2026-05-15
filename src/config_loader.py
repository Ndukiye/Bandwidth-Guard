import yaml
import os

# ALWAYS use /var/lib/bandwidth-guard
CONFIG_PATH = "/var/lib/bandwidth-guard/config.yaml"

def load_enforcement_config():
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
    # Ensure directory exists
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    
    with open(CONFIG_PATH, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)

def get_data_plan():
    config = load_enforcement_config()
    return config.get('global', {}).get('data_plan', 'Not configured')

def set_data_plan(plan_name, limit_mb):
    config = load_enforcement_config()
    
    if 'global' not in config:
        config['global'] = {}
    
    config['global']['data_plan'] = plan_name
    config['global']['daily_limit_mb'] = limit_mb
    
    save_limit_config(config)