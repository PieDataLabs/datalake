import os
import json


def load_credentials():
    home_dir = os.path.expanduser('~')
    pielake_dir = os.path.join(home_dir, ".pielake")
    credentials_path = os.path.join(pielake_dir, "credentials.json")
    if not os.path.exists(credentials_path):
        return None
    with open(credentials_path, 'r') as f:
        credentials = json.load(f)
    if "api_key" not in credentials or "email" not in credentials:
        return None
    if len(credentials["api_key"]) != 32:
        return None

    return credentials


def save_credentials(email, api_key):
    home_dir = os.path.expanduser('~')
    pielake_dir = os.path.join(home_dir, ".pielake")
    credentials_path = os.path.join(pielake_dir, "credentials.json")
    os.makedirs(pielake_dir, exist_ok=True)
    with open(credentials_path, 'w') as f:
        json.dump({
            "email": email,
            "api_key": api_key
        }, f)
