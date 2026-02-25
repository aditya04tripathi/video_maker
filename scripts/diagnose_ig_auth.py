import sys
import os
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.services.instagram import InstagramGraphClient
from src.core.logger import Log
from src.config.settings import settings

def main():
    Log.info("=== Instagram Authentication & Ownership Diagnostic ===")
    
    client = InstagramGraphClient()
    
    Log.info(f"Current API Version: {settings.ig_api_version}")
    Log.info(f"Current User ID: {settings.ig_user_id}")
    Log.info(f"Configured App ID: {settings.ig_app_id or 'Not Set'}")
    
    # Check Token Info
    token_info = client.get_token_info()
    if not token_info:
        Log.error("FATAL: Token is invalid or expired.")
        return
    
    user_data = token_info.get("user", {})
    app_data = token_info.get("app", {})
    
    Log.info("--- Token Information ---")
    Log.info(f"Authorized User: {user_data.get('name')} (ID: {user_data.get('id')})")
    if app_data:
        Log.info(f"Authorized App: {app_data.get('name')} (ID: {app_data.get('id')})")
        
        if settings.ig_app_id and app_data.get('id') != settings.ig_app_id:
            Log.error(f"MISMATCH: Token belongs to App ID {app_data.get('id')}, but you configured {settings.ig_app_id}!")
        else:
            Log.info("SUCCESS: Token and App ID configuration are consistent.")
    else:
        Log.warning("Could not retrieve App information for this token.")
        Log.info("This might happen if the token doesn't have 'ads_management' or similar permissions, or if it's a client-side token.")

    # Optional: Test a container ID if provided as argument
    if len(sys.argv) > 1:
        container_id = sys.argv[1]
        Log.info(f"--- Container Ownership Check: {container_id} ---")
        is_valid = client.validate_app_ownership(container_id)
        if is_valid:
            Log.info(f"SUCCESS: Token has ownership/access to container {container_id}.")
        else:
            Log.error(f"FAILURE: Token DOES NOT have access to container {container_id}.")
            Log.error("This usually means the container was created using a DIFFERENT App ID than the current token.")

    Log.info("=== Diagnostic Complete ===")

if __name__ == "__main__":
    main()
