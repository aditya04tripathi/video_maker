import requests
import time
import os
from src.core.logger import Log
from src.config.settings import settings

class InstagramGraphClient:
    def __init__(self):
        self.access_token = settings.ig_access_token
        self.user_id = settings.ig_user_id
        self.app_id = settings.ig_app_id
        self.api_version = settings.ig_api_version
        self.base_url = f"https://graph.facebook.com/{self.api_version}"
        self.upload_url = "https://rupload.facebook.com/ig-api-upload"

    def _handle_api_error(self, response: requests.Response, context: str):
        """Helper to log detailed error info and handle specific cases like App ID mismatch"""
        Log.error(f"Error during {context}. Status: {response.status_code}")
        Log.error(f"Error Body: {response.text}")
        
        if response.status_code == 400:
            error_data = response.json().get("error", {})
            error_msg = error_data.get("message", "")
            if "App ID mismatch" in error_msg:
                Log.error(
                    "CRITICAL: App ID Mismatch detected! Verify that your token "
                    f"was generated for App ID {settings.ig_app_id or '1421434496123015'}."
                )

    def upload_reel(self, video_url: str, caption: str, cover_url: str = None) -> str:
        """
        Uploads a reel using a public URL (Standard Video Upload).
        """
        try:
            Log.info(f"Initializing URL upload session for Reel: {video_url[:50]}...")
            
            # Diagnostic: Check for internal URLs that Instagram cannot reach
            is_video_internal = any(x in video_url for x in ["railway.internal", "localhost", "127.0.0.1"])
            if is_video_internal:
                Log.error(f"The video_url provided is an internal URL: {video_url}. Instagram will fail to fetch this.")
                return None

            url = f"{self.base_url}/{self.user_id}/media"
            
            payload = {
                "media_type": "REELS",
                "video_url": video_url,
                "caption": caption,
                "access_token": self.access_token,
                "share_to_feed": "true"
            }

            if cover_url:
                is_internal = any(x in cover_url for x in ["railway.internal", "localhost", "127.0.0.1"])
                if is_internal:
                    Log.warning("The cover_url provided is an internal URL. Skipping cover_url.")
                else:
                    Log.info(f"Setting cover image from: {cover_url}")
                    payload["cover_url"] = cover_url
            
            response = requests.post(url, json=payload)
            
            if not response.ok:
                self._handle_api_error(response, "URL upload initialization")
            
            response.raise_for_status()
            
            data = response.json()
            container_id = data.get("id")
            
            Log.info(f"Upload session initialized. Container ID: {container_id}")
            return container_id

        except Exception as e:
            Log.error(f"Failed to upload reel via URL: {e}")
            return None

    def upload_image(self, image_url: str, caption: str) -> str:
        """
        Uploads a single image post using a public URL.
        """
        try:
            Log.info("Initializing Image upload session...")
            url = f"{self.base_url}/{self.user_id}/media"
            
            payload = {
                "image_url": image_url,
                "caption": caption,
                "access_token": self.access_token
            }
            
            response = requests.post(url, json=payload)
            
            if not response.ok:
                self._handle_api_error(response, "Image upload initialization")
            
            response.raise_for_status()
            
            data = response.json()
            container_id = data.get("id")
            
            Log.info(f"Image upload session initialized. Container ID: {container_id}")
            return container_id

        except Exception as e:
            Log.error(f"Failed to upload image via URL: {e}")
            return None

    def upload_reel_binary(self, video_path: str, caption: str, cover_url: str = None) -> str:
        """
        Uploads a reel using the resumable upload protocol (binary upload).
        Handles chunked streaming for reliability and performance.
        """
        try:
            # Step 1: Initialize Upload Session
            Log.info("Initializing binary upload session...")
            init_url = f"{self.base_url}/{self.user_id}/media"
            
            params = {
                "access_token": self.access_token
            }
            
            init_payload = {
                "media_type": "REELS",
                "upload_type": "resumable",
                "caption": caption,
                "share_to_feed": "true"
            }

            if cover_url:
                is_internal = any(x in cover_url for x in ["railway.internal", "localhost", "127.0.0.1"])
                if not is_internal:
                    Log.info(f"Setting cover image from: {cover_url}")
                    init_payload["cover_url"] = cover_url
            
            response = requests.post(init_url, json=init_payload, params=params)
            if not response.ok:
                self._handle_api_error(response, "binary upload initialization")
            response.raise_for_status()
            
            data = response.json()
            container_id = data.get("id")
            upload_uri = data.get("uri")
            
            if not upload_uri:
                upload_uri = f"{self.upload_url}/{container_id}"
                Log.info(f"Using constructed upload URI: {upload_uri}")
            else:
                Log.info(f"Using API provided upload URI: {upload_uri}")
            
            Log.info(f"Upload session initialized. Container ID: {container_id}")

            # Step 2: Upload Binary Data using chunked streaming
            file_size = os.path.getsize(video_path)
            Log.info(f"Uploading binary data ({file_size / (1024*1024):.2f} MB) in chunks...")
            
            # Match the official documentation exactly:
            # - Use Authorization: OAuth <ACCESS_TOKEN>
            # - Include offset and file_size
            # - Some implementations require X-FB-App-ID explicitly
            headers = {
                "Authorization": f"OAuth {self.access_token}",
                "offset": "0",
                "file_size": str(file_size),
                "X-FB-App-ID": self.app_id
            }
            
            # Use a chunk size of 4MB (Instagram recommends between 1MB and 1GB)
            chunk_size = 4 * 1024 * 1024
            offset = 0
            
            with open(video_path, "rb") as f:
                while offset < file_size:
                    # Check server offset to handle potential state loss
                    if offset > 0:
                        try:
                            # Resumable protocol: check current offset
                            check_res = requests.get(
                                upload_uri, 
                                headers={
                                    "Authorization": f"OAuth {self.access_token}",
                                    "X-FB-App-ID": self.app_id
                                }, 
                                timeout=10
                            )
                            if check_res.ok:
                                server_offset = int(check_res.json().get("offset", offset))
                                if server_offset != offset:
                                    Log.warning(f"Offset mismatch! Local: {offset}, Server: {server_offset}. Adjusting...")
                                    offset = server_offset
                                    f.seek(offset)
                        except Exception as check_err:
                            Log.warning(f"Failed to check server offset: {check_err}")

                    f.seek(offset)
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                        
                    headers["offset"] = str(offset)
                    
                    for attempt in range(3):
                        try:
                            # Perform the chunk upload POST
                            response = requests.post(upload_uri, headers=headers, data=chunk, timeout=60)
                            if response.ok:
                                break
                            
                            # Handle OffsetInvalidError by checking server offset
                            if response.status_code == 412 or "OffsetInvalidError" in response.text:
                                Log.warning(f"Offset error detected. Checking server state (attempt {attempt+1})...")
                                check_res = requests.get(
                                    upload_uri, 
                                    headers={
                                        "Authorization": f"OAuth {self.access_token}",
                                        "X-FB-App-ID": self.app_id
                                    }, 
                                    timeout=10
                                )
                                if check_res.ok:
                                    server_offset = int(check_res.json().get("offset", 0))
                                    Log.warning(f"Server reported offset: {server_offset}. Retrying chunk from there.")
                                    offset = server_offset
                                    f.seek(offset)
                                    headers["offset"] = str(offset)
                                    chunk = f.read(chunk_size)
                            else:
                                Log.warning(f"Chunk upload failed (attempt {attempt+1}): {response.text}")
                        except Exception as ce:
                            Log.warning(f"Chunk upload error (attempt {attempt+1}): {ce}")
                        
                        if attempt < 2:
                            time.sleep(2 ** attempt)
                    
                    if not response.ok:
                        self._handle_api_error(response, "binary chunk upload")
                        response.raise_for_status()
                        
                    offset += len(chunk)
                    progress = (offset / file_size) * 100
                    Log.info(f"Upload progress: {progress:.1f}% ({offset}/{file_size} bytes)")
                
            Log.info("Binary upload completed successfully.")
            return container_id

        except Exception as e:
            Log.error(f"Failed to upload reel binary: {e}")
            return None

    def check_status(self, container_id: str) -> str:
        """Check the status of the media container"""
        url = f"{self.base_url}/{container_id}"
        params = {
            "fields": "id,status_code",
            "access_token": self.access_token
        }
        
        try:
            response = requests.get(url, params=params)
            
            data = response.json()
            status = data.get("status_code")
            
            if status is None:
                Log.info(f"Container {container_id} has no status_code yet. Still initializing...")
                return "IN_PROGRESS"

            if status == "ERROR":
                Log.error(f"Container {container_id} failed.")
            elif status == "FINISHED":
                Log.info(f"Container {container_id} is ready.")
                
            return status
        except Exception as e:
            Log.error(f"Failed to check status: {e}")
            return "ERROR"

    def publish_media(self, container_id: str) -> str:
        """Publish the media container"""
        url = f"{self.base_url}/{self.user_id}/media_publish"
        payload = {
            "creation_id": container_id,
            "access_token": self.access_token
        }
        
        try:
            Log.info(f"Publishing container: {container_id}")
            response = requests.post(url, json=payload)
            if not response.ok:
                self._handle_api_error(response, "media publishing")
            response.raise_for_status()
            media_id = response.json().get("id")
            Log.info(f"Successfully published media: {media_id}")
            return media_id
        except Exception as e:
            Log.error(f"Failed to publish media: {e}")
            return None

    def get_media_permalink(self, media_id: str) -> str:
        """Get the permalink of a published media item"""
        url = f"{self.base_url}/{media_id}"
        params = {
            "fields": "permalink",
            "access_token": self.access_token
        }
        try:
            response = requests.get(url, params=params)
            if not response.ok:
                self._handle_api_error(response, "getting permalink")
            response.raise_for_status()
            return response.json().get("permalink")
        except Exception as e:
            Log.error(f"Failed to get permalink for media {media_id}: {e}")
            return None

    def wait_and_publish(self, container_id: str, max_retries=30, delay=10) -> str:
        """
        Polls for container status and publishes when ready.
        Matches the robust polling logic in direct_reel_uploader.py.
        """
        for i in range(max_retries):
            status = self.check_status(container_id)
            Log.info(f"Container status ({i+1}/{max_retries}): {status}")
            
            if status == "FINISHED":
                Log.info("Container ready for publishing.")
                media_id = self.publish_media(container_id)
                if media_id:
                    permalink = self.get_media_permalink(media_id)
                    return permalink
                else:
                    Log.error("Publishing failed after processing finished.")
                    return None
            
            if status == "ERROR":
                Log.error("Container processing failed on Instagram side.")
                return None
                
            time.sleep(delay)
        
        Log.error(f"Timeout: Container {container_id} not ready after {max_retries * delay} seconds.")
        return None

    def get_token_info(self) -> dict:
        """
        Retrieves information about the current access token, including the App ID.
        Uses the /me endpoint to check basic validity and /app to get app details.
        """
        try:
            # First, check /me to see if token is valid
            me_url = f"{self.base_url}/me"
            me_params = {"access_token": self.access_token, "fields": "id,name"}
            me_res = requests.get(me_url, params=me_params)
            
            if not me_res.ok:
                Log.error(f"Token validation failed: {me_res.text}")
                return None
            
            me_data = me_res.json()
            
            # Diagnostic: Token Scopes
            scopes_url = f"https://graph.facebook.com/debug_token"
            scopes_params = {
                "input_token": self.access_token,
                "access_token": self.access_token # Using same token as app-token for simplicity if it's a system user or long-lived token
            }
            # Note: debug_token usually needs an App Access Token. 
            # If this fails, we just log it.
            
            # Now, check /app to get the App ID
            app_url = f"{self.base_url}/app"
            app_params = {"access_token": self.access_token, "fields": "id,name,namespace"}
            app_res = requests.get(app_url, params=app_params)
            
            if not app_res.ok:
                Log.error(f"Failed to fetch App info: {app_res.text}")
                return {"user": me_data, "app": None}
            
            app_data = app_res.json()
            return {"user": me_data, "app": app_data}
            
        except Exception as e:
            Log.error(f"Error fetching token info: {e}")
            return None

    def validate_app_ownership(self, container_id: str = None) -> bool:
        """
        Verifies that the current token and (optional) container ID share the same App ID ownership.
        """
        Log.info("Verifying App ID and ownership consistency...")
        
        token_info = self.get_token_info()
        if not token_info:
            Log.error("Could not retrieve token info. Token might be invalid.")
            return False
        
        app_id = token_info.get("app", {}).get("id")
        Log.info(f"Token belongs to App ID: {app_id} ({token_info.get('app', {}).get('name')})")
        
        # If we have a configured App ID, check for match
        if settings.ig_app_id and app_id != settings.ig_app_id:
            Log.warning(f"Configured IG_APP_ID ({settings.ig_app_id}) does not match token's App ID ({app_id})!")
            # We don't necessarily return False here, but we warn the user.
        
        # If container_id is provided, try to verify if this token can access it
        if container_id:
            Log.info(f"Verifying access to container: {container_id}...")
            url = f"{self.base_url}/{container_id}"
            params = {"fields": "id", "access_token": self.access_token}
            res = requests.get(url, params=params)
            
            if not res.ok:
                if "App ID mismatch" in res.text:
                    Log.error(f"OWNERSHIP MISMATCH: Container {container_id} was created by a different App than this token!")
                    return False
                Log.error(f"Could not access container {container_id}: {res.text}")
                return False
            
            Log.info(f"Ownership verified. Token has access to container {container_id}.")
            
        return True
