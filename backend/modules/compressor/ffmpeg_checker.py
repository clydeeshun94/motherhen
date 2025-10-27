import subprocess
import sys
import os
import platform
from typing import Tuple, Optional

class FFmpegChecker:
    """
    A utility class to check for FFmpeg installation and install it if needed.
    """
    
    @staticmethod
    def is_ffmpeg_installed() -> Tuple[bool, Optional[str]]:
        """
        Check if FFmpeg is installed and accessible.
        
        Returns:
            Tuple of (is_installed, error_message)
        """
        try:
            # Try to run ffmpeg command
            result = subprocess.run(
                ['ffmpeg', '-version'], 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL,
                check=True
            )
            
            # Try to run ffprobe command
            result = subprocess.run(
                ['ffprobe', '-version'], 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL,
                check=True
            )
            
            return True, None
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            return False, str(e)
    
    @staticmethod
    def get_installation_instructions() -> str:
        """
        Get platform-specific installation instructions for FFmpeg.
        
        Returns:
            Installation instructions as a string
        """
        system = platform.system().lower()
        
        if system == "darwin":  # macOS
            return """
FFmpeg installation options for macOS:
1. Using Homebrew (recommended):
   brew install ffmpeg

2. Using MacPorts:
   sudo port install ffmpeg

3. Download pre-compiled binaries:
   Visit https://evermeet.cx/ffmpeg/ and download the latest version
   Then extract and move binaries to /usr/local/bin/
   
4. Manual compilation:
   Download source from https://ffmpeg.org/download.html
   Follow compilation instructions at https://trac.ffmpeg.org/wiki/CompilationGuide/macOS
"""
        elif system == "linux":
            return """
FFmpeg installation options for Linux:
1. Ubuntu/Debian:
   sudo apt update && sudo apt install ffmpeg

2. CentOS/RHEL/Fedora:
   sudo yum install epel-release && sudo yum install ffmpeg
   OR
   sudo dnf install ffmpeg

3. Arch Linux:
   sudo pacman -S ffmpeg
"""
        elif system == "windows":
            return """
FFmpeg installation options for Windows:
1. Download from https://ffmpeg.org/download.html
2. Extract the archive
3. Add the 'bin' directory to your system PATH
"""
        else:
            return f"Please visit https://ffmpeg.org/download.html to download FFmpeg for your system ({system})"
    
    @staticmethod
    def check_and_report() -> dict:
        """
        Check FFmpeg installation and return a detailed report.
        
        Returns:
            Dictionary with installation status and information
        """
        is_installed, error = FFmpegChecker.is_ffmpeg_installed()
        
        report = {
            'installed': is_installed,
            'error': error,
            'system': platform.system(),
            'instructions': FFmpegChecker.get_installation_instructions()
        }
        
        if is_installed:
            # Get version information
            try:
                ffmpeg_version = subprocess.run(
                    ['ffmpeg', '-version'], 
                    capture_output=True, 
                    text=True
                )
                report['ffmpeg_version'] = ffmpeg_version.stdout.split('\n')[0] if ffmpeg_version.stdout else "Unknown"
                
                ffprobe_version = subprocess.run(
                    ['ffprobe', '-version'], 
                    capture_output=True, 
                    text=True
                )
                report['ffprobe_version'] = ffprobe_version.stdout.split('\n')[0] if ffprobe_version.stdout else "Unknown"
            except Exception as e:
                report['version_error'] = str(e)
        
        return report

# Convenience function for easy checking
def check_ffmpeg() -> dict:
    """
    Check FFmpeg installation status.
    
    Returns:
        Dictionary with installation status and information
    """
    return FFmpegChecker.check_and_report()

if __name__ == "__main__":
    # Run the check when executed directly
    report = check_ffmpeg()
    
    if report['installed']:
        print("✅ FFmpeg is properly installed")
        print(f"FFmpeg version: {report.get('ffmpeg_version', 'Unknown')}")
        print(f"FFprobe version: {report.get('ffprobe_version', 'Unknown')}")
    else:
        print("❌ FFmpeg is not installed or not accessible")
        print(f"Error: {report['error']}")
        print("\nInstallation instructions:")
        print(report['instructions'])