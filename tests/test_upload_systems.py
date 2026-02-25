import sys
import os
import time
import requests
import unittest
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.getcwd())

from src.services.instagram import InstagramGraphClient
from src.services.storage import MinIOClient
from src.config.settings import settings

class TestUploadSystems(unittest.TestCase):
    def setUp(self):
        self.ig_client = InstagramGraphClient()
        self.test_video = str(settings.audio_track_path) # Use audio_track.mp4 as a dummy binary file
        self.caption = "Test upload"

    @patch('requests.post')
    def test_binary_upload_init(self, mock_post):
        """Test binary upload initialization"""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {"id": "12345", "uri": "http://upload.uri"}
        mock_post.return_value = mock_response
        
        container_id = self.ig_client.upload_reel_binary(self.test_video, self.caption)
        self.assertEqual(container_id, "12345")
        
    @patch('requests.post')
    @patch('os.path.getsize')
    def test_binary_upload_streaming(self, mock_getsize, mock_post):
        """Test binary upload streaming logic"""
        mock_getsize.return_value = 100 # small file for testing
        
        # Mock init response
        mock_init = MagicMock()
        mock_init.ok = True
        mock_init.json.return_value = {"id": "12345", "uri": "http://upload.uri"}
        
        # Mock chunk upload response
        mock_chunk = MagicMock()
        mock_chunk.ok = True
        
        mock_post.side_effect = [mock_init, mock_chunk]
        
        container_id = self.ig_client.upload_reel_binary(self.test_video, self.caption)
        self.assertEqual(container_id, "12345")
        # Ensure at least 2 POST calls (1 init, 1 chunk)
        self.assertGreaterEqual(mock_post.call_count, 2)

    def test_minio_vs_binary_logic(self):
        """Benchmark/Compare Logic (Simulation)"""
        # MinIO requires: Upload to MinIO -> Get URL -> Instagram fetches URL
        # Binary requires: Direct Stream to Instagram
        
        # Simulation of network calls
        minio_steps = ["Upload to MinIO", "Presign URL", "Instagram Fetch (External)"]
        binary_steps = ["Direct Stream to Instagram"]
        
        print(f"\nArchitecture Comparison:")
        print(f"MinIO Flow: {' -> '.join(minio_steps)}")
        print(f"Binary Flow: {' -> '.join(binary_steps)}")
        print(f"Binary advantage: Reduced latency, no external fetch dependency, better reliability.")

if __name__ == "__main__":
    unittest.main()
