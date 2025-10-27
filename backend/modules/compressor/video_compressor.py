import os
import uuid
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
import json

class VideoCompressor:
    """
    A video compression utility using FFmpeg
    """
    
    def __init__(self, upload_dir: str = "uploads", compressed_dir: str = "compressed"):
        """
        Initialize the video compressor
        
        Args:
            upload_dir: Directory to store uploaded videos
            compressed_dir: Directory to store compressed videos
        """
        self.upload_dir = Path(upload_dir)
        self.compressed_dir = Path(compressed_dir)
        
        # Create directories if they don't exist
        self.upload_dir.mkdir(exist_ok=True)
        self.compressed_dir.mkdir(exist_ok=True)
        
        # Check if FFmpeg is installed and try to install if needed
        self._check_and_install_ffmpeg()
        
        # Compression presets
        self.presets = {
            "low": {
                "crf": 28,  # Higher CRF = more compression
                "preset": "fast",
                "audio_bitrate": "64k"
            },
            "medium": {
                "crf": 23,
                "preset": "medium", 
                "audio_bitrate": "128k"
            },
            "high": {
                "crf": 18,  # Lower CRF = better quality
                "preset": "slow",
                "audio_bitrate": "192k"
            }
        }
    
    def _check_and_install_ffmpeg(self):
        """Check if FFmpeg is installed and install it if needed"""
        try:
            # Try to import and use the installer
            from src.ffmpeg_installer import FFmpegInstaller
            installer = FFmpegInstaller()
            
            # Check if already installed in our directory
            if not installer.is_installed():
                print("FFmpeg not found. Attempting to install automatically...")
                if not installer.download_and_install():
                    raise Exception("Failed to automatically install FFmpeg")
                print("✅ FFmpeg installed successfully")
            
            # Add to PATH
            installer._add_to_path()
            
        except ImportError:
            # Fallback to basic check
            try:
                subprocess.run(['ffmpeg', '-version'], 
                             stdout=subprocess.DEVNULL, 
                             stderr=subprocess.DEVNULL,
                             check=True)
                subprocess.run(['ffprobe', '-version'], 
                             stdout=subprocess.DEVNULL, 
                             stderr=subprocess.DEVNULL,
                             check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                raise Exception("FFmpeg is not installed and could not be installed automatically. "
                               "Please install FFmpeg manually:\n"
                               "- macOS: brew install ffmpeg\n"
                               "- Ubuntu/Debian: sudo apt update && sudo apt install ffmpeg\n"
                               "- Windows: Download from https://ffmpeg.org/download.html")
    
    def get_video_info(self, file_path: Path) -> Dict[str, Any]:
        """
        Get video information using FFprobe
        
        Args:
            file_path: Path to the video file
            
        Returns:
            Dictionary with video information
        """
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            str(file_path)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            info = json.loads(result.stdout)
            
            # Extract relevant information
            video_info = {
                'duration': float(info['format'].get('duration', 0)),
                'size': int(info['format'].get('size', 0)),
                'bitrate': int(info['format'].get('bit_rate', 0)),
                'format': info['format'].get('format_name', 'unknown'),
            }
            
            # Get video stream info
            video_stream = next((s for s in info['streams'] if s['codec_type'] == 'video'), None)
            if video_stream:
                video_info.update({
                    'width': video_stream.get('width'),
                    'height': video_stream.get('height'),
                    'codec': video_stream.get('codec_name'),
                    'fps': video_stream.get('avg_frame_rate')
                })
            
            return video_info
            
        except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError) as e:
            raise Exception(f"Failed to get video info: {str(e)}")
        except FileNotFoundError:
            raise Exception("FFprobe not found. Please ensure FFmpeg is properly installed.")
    
    def compress_video(self, 
                      input_path: Path, 
                      output_path: Path, 
                      compression_level: str = "medium",
                      target_size_mb: Optional[int] = None) -> None:
        """
        Compress video using FFmpeg with different quality levels
        
        Args:
            input_path: Path to input video file
            output_path: Path to output compressed video file
            compression_level: Compression level (low, medium, high)
            target_size_mb: Target file size in MB (optional)
        """
        if compression_level not in self.presets:
            raise ValueError(f"Invalid compression level. Choose from: {list(self.presets.keys())}")
        
        preset = self.presets[compression_level]
        
        # Base FFmpeg command
        cmd = [
            'ffmpeg',
            '-i', str(input_path),
            '-c:v', 'libx264',
            '-crf', str(preset['crf']),
            '-preset', preset['preset'],
            '-c:a', 'aac',
            '-b:a', preset['audio_bitrate'],
            '-y',  # Overwrite output file
            str(output_path)
        ]
        
        try:
            # For target size, we would need two-pass encoding
            if target_size_mb:
                # Calculate required bitrate for target file size
                video_info = self.get_video_info(input_path)
                target_bitrate = self._calculate_bitrate(video_info['duration'], target_size_mb)
                
                # Two-pass encoding for target size (more accurate)
                # First pass
                pass1_cmd = cmd.copy()
                pass1_cmd[1:1] = ['-b:v', f'{target_bitrate}k']  # Insert after -i
                pass1_cmd.extend(['-pass', '1', '-f', 'null'])
                pass1_cmd.append('/dev/null' if os.name != 'nt' else 'NUL')
                
                # Second pass  
                pass2_cmd = cmd.copy()
                pass2_cmd[1:1] = ['-b:v', f'{target_bitrate}k']  # Insert after -i
                pass2_cmd.extend(['-pass', '2'])
                
                # Run two-pass encoding
                subprocess.run(pass1_cmd, check=True, capture_output=True)
                subprocess.run(pass2_cmd, check=True, capture_output=True)
            else:
                # Single pass with CRF
                subprocess.run(cmd, check=True, capture_output=True)
                
        except subprocess.CalledProcessError as e:
            raise Exception(f"Video compression failed: {e.stderr.decode() if e.stderr else str(e)}")
        except FileNotFoundError:
            raise Exception("FFmpeg not found. Please ensure FFmpeg is properly installed.")
    
    def _calculate_bitrate(self, duration: float, target_size_mb: int) -> int:
        """
        Calculate required bitrate for target file size
        
        Args:
            duration: Video duration in seconds
            target_size_mb: Target file size in MB
            
        Returns:
            Video bitrate in kbps
        """
        # Calculate bitrate (in kbps)
        target_size_kb = target_size_mb * 1024
        audio_bitrate = 128  # Assume 128kbps for audio
        video_bitrate = int((target_size_kb * 8 / duration) - audio_bitrate)
        
        return max(video_bitrate, 500)  # Minimum 500kbps
    
    def process_video(self, 
                     input_file_path: str, 
                     compression_level: str = "medium",
                     target_size_mb: Optional[int] = None) -> Dict[str, Any]:
        """
        Process a video file - compress and return information
        
        Args:
            input_file_path: Path to the input video file
            compression_level: Compression level (low, medium, high)
            target_size_mb: Target file size in MB (optional)
            
        Returns:
            Dictionary with processing results
        """
        input_path = Path(input_file_path)
        
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_file_path}")
        
        # Generate unique filename for output
        file_id = str(uuid.uuid4())
        original_filename = input_path.name
        output_filename = f"compressed_{file_id}_{original_filename}"
        output_path = self.compressed_dir / output_filename
        
        try:
            # Get original file info
            original_info = self.get_video_info(input_path)
            
            # Compress video
            self.compress_video(input_path, output_path, compression_level, target_size_mb)
            
            # Get compressed file info
            compressed_info = self.get_video_info(output_path)
            
            # Calculate compression ratio
            original_size_mb = original_info['size'] / (1024 * 1024)
            compressed_size_mb = compressed_info['size'] / (1024 * 1024)
            compression_ratio = (1 - compressed_size_mb / original_size_mb) * 100 if original_size_mb > 0 else 0
            
            return {
                "file_id": file_id,
                "original_filename": original_filename,
                "original_size_mb": round(original_size_mb, 2),
                "compressed_size_mb": round(compressed_size_mb, 2),
                "compression_ratio": round(compression_ratio, 2),
                "output_path": str(output_path),
                "original_info": original_info,
                "compressed_info": compressed_info
            }
            
        except Exception as e:
            # Clean up on error
            if output_path.exists():
                output_path.unlink()
            raise Exception(f"Video processing failed: {str(e)}")