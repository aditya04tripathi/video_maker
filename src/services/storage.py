import boto3
from botocore.exceptions import NoCredentialsError, ClientError
import os
from src.core.logger import Log
from src.config.settings import settings

class MinIOClient:
    def __init__(self):
        # Use S3_PUBLIC_URL as a fallback for the endpoint if S3_ENDPOINT_URL is not set
        endpoint = settings.s3_endpoint_url or settings.s3_public_url
        
        self.s3_client = boto3.client(
            's3',
            endpoint_url=endpoint,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            region_name=settings.s3_region
        )
        self.bucket_name = settings.s3_bucket_name
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """Checks if the bucket exists, and creates it if it doesn't"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            Log.info(f"Bucket '{self.bucket_name}' already exists.")
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code')
            if error_code == '404' or error_code == 'NoSuchBucket':
                Log.info(f"Bucket '{self.bucket_name}' not found. Creating it...")
                try:
                    self.s3_client.create_bucket(Bucket=self.bucket_name)
                    Log.info(f"Bucket '{self.bucket_name}' created successfully.")
                except Exception as create_err:
                    Log.error(f"Failed to create bucket '{self.bucket_name}': {create_err}")
            else:
                Log.error(f"Error checking bucket existence: {e}")

    def upload_file(self, file_path: str, object_name: str = None) -> bool:
        """Upload a file to an S3 bucket with automatic content-type detection"""
        if object_name is None:
            object_name = os.path.basename(file_path)

        # Detect content type
        import mimetypes
        content_type, _ = mimetypes.guess_type(file_path)
        if not content_type:
            if file_path.endswith('.jpg') or file_path.endswith('.jpeg'):
                content_type = 'image/jpeg'
            elif file_path.endswith('.mp4'):
                content_type = 'video/mp4'
            else:
                content_type = 'application/octet-stream'

        try:
            extra_args = {'ContentType': content_type}
            self.s3_client.upload_file(
                file_path, 
                self.bucket_name, 
                object_name,
                ExtraArgs=extra_args
            )
            Log.info(f"Successfully uploaded {file_path} to {self.bucket_name}/{object_name} (Type: {content_type})")
            return True
        except FileNotFoundError:
            Log.error(f"The file was not found: {file_path}")
            return False
        except NoCredentialsError:
            Log.error("Credentials not available")
            return False
        except ClientError as e:
            Log.error(f"ClientError during upload: {e}")
            return False

    def get_presigned_url(self, object_name: str, expiration=3600) -> str:
        """Generate a presigned URL to share an S3 object"""
        try:
            response = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': object_name},
                ExpiresIn=expiration
            )
            
            # Use public URL if configured (e.g., for Railway or external access)
            if settings.s3_public_url and settings.s3_endpoint_url:
                response = response.replace(settings.s3_endpoint_url, settings.s3_public_url)
            
            Log.info(f"Generated presigned URL for {object_name}")
            return response
        except ClientError as e:
            Log.error(f"ClientError generating presigned URL: {e}")
            return None

    def delete_file(self, object_name: str) -> bool:
        """Delete a file from an S3 bucket"""
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=object_name)
            Log.info(f"Successfully deleted {object_name} from {self.bucket_name}")
            return True
        except ClientError as e:
            Log.error(f"ClientError during deletion: {e}")
            return False
