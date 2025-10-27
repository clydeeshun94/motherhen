import os
import sys
import platform
import subprocess
import urllib.request
import zipfile
import tarfile
import shutil
from pathlib import Path
import tempfile

class FFmpegInstaller:
    """
    Automatically download and install FFmpeg for the application
    """
    
    def __init__(self, install_dir=None):
        """
        Initialize the FFmpeg installer
        
        Args:
            install_dir: Directory to install FFmpeg (default: app directory)
        """
        if install_dir is None:
            # Install in the app's ffmpeg directory
            self.install_dir = Path(__file__).parent.parent / "ffmpeg"
        else:
            self.install_dir = Path(install_dir)
        
        self.install_dir.mkdir(parents=True, exist_ok=True)
        self.bin_dir = self.install_dir / "bin"
        self.bin_dir.mkdir(exist_ok=True)
        
        # Add to PATH
        self._add_to_path()
    
    def _add_to_path(self):
        """Add FFmpeg bin directory to PATH"""
        bin_path = str(self.bin_dir.absolute())
        if bin_path not in os.environ.get('PATH', ''):
            os.environ['PATH'] = bin_path + os.pathsep + os.environ.get('PATH', '')
    
    def is_installed(self):
        """Check if FFmpeg is installed in our directory"""
        ffmpeg_path = self.bin_dir / ("ffmpeg.exe" if platform.system() == "Windows" else "ffmpeg")
        ffprobe_path = self.bin_dir / ("ffprobe.exe" if platform.system() == "Windows" else "ffprobe")
        
        return ffmpeg_path.exists() and ffprobe_path.exists()
    
    def get_ffmpeg_version(self):
        """Get installed FFmpeg version"""
        if not self.is_installed():
            return None
            
        try:
            ffmpeg_path = self.bin_dir / ("ffmpeg.exe" if platform.system() == "Windows" else "ffmpeg")
            result = subprocess.run(
                [str(ffmpeg_path), "-version"], 
                capture_output=True, 
                text=True, 
                check=True
            )
            return result.stdout.split('\n')[0]
        except Exception:
            return None
    
    def download_and_install(self):
        """
        Download and install FFmpeg automatically
        
        Returns:
            bool: True if successful, False otherwise
        """
        system = platform.system().lower()
        
        try:
            if system == "darwin":  # macOS
                return self._install_macos()
            elif system == "windows":
                return self._install_windows()
            elif system == "linux":
                return self._install_linux()
            else:
                print(f"Unsupported system: {system}")
                return False
        except Exception as e:
            print(f"Error installing FFmpeg: {e}")
            return False
    
    def _install_macos(self):
        """Install FFmpeg on macOS using a static build"""
        print("Downloading FFmpeg for macOS...")
        
        # Try to download from evermeet.cx (known reliable source)
        ffmpeg_url = "https://evermeet.cx/ffmpeg/ffmpeg-6.0.zip"
        ffprobe_url = "https://evermeet.cx/ffmpeg/ffprobe-6.0.zip"
        
        try:
            # Download FFmpeg
            ffmpeg_zip = self.install_dir / "ffmpeg.zip"
            urllib.request.urlretrieve(ffmpeg_url, ffmpeg_zip)
            
            # Extract
            with zipfile.ZipFile(ffmpeg_zip, 'r') as zip_ref:
                zip_ref.extractall(self.bin_dir)
            
            # Make executable
            ffmpeg_bin = self.bin_dir / "ffmpeg"
            ffmpeg_bin.chmod(0o755)
            
            # Download FFprobe
            ffprobe_zip = self.install_dir / "ffprobe.zip"
            urllib.request.urlretrieve(ffprobe_url, ffprobe_zip)
            
            # Extract
            with zipfile.ZipFile(ffprobe_zip, 'r') as zip_ref:
                zip_ref.extractall(self.bin_dir)
            
            # Make executable
            ffprobe_bin = self.bin_dir / "ffprobe"
            ffprobe_bin.chmod(0o755)
            
            # Clean up
            ffmpeg_zip.unlink()
            ffprobe_zip.unlink()
            
            return self.is_installed()
            
        except Exception as e:
            print(f"Error downloading FFmpeg for macOS: {e}")
            # Try alternative method
            return self._install_with_brew()
    
    def _install_with_brew(self):
        """Try to install FFmpeg using Homebrew if available"""
        try:
            # Check if Homebrew is installed
            subprocess.run(["brew", "--version"], 
                          check=True, 
                          stdout=subprocess.DEVNULL, 
                          stderr=subprocess.DEVNULL)
            
            print("Installing FFmpeg with Homebrew...")
            # Install FFmpeg
            subprocess.run(["brew", "install", "ffmpeg"], check=True)
            
            # Find and copy binaries
            result = subprocess.run(["brew", "--prefix", "ffmpeg"], 
                                  capture_output=True, 
                                  text=True, 
                                  check=True)
            brew_prefix = Path(result.stdout.strip())
            
            # Copy binaries to our directory
            src_ffmpeg = brew_prefix / "bin" / "ffmpeg"
            src_ffprobe = brew_prefix / "bin" / "ffprobe"
            
            if src_ffmpeg.exists() and src_ffprobe.exists():
                shutil.copy(src_ffmpeg, self.bin_dir)
                shutil.copy(src_ffprobe, self.bin_dir)
                
                # Make executable
                (self.bin_dir / "ffmpeg").chmod(0o755)
                (self.bin_dir / "ffprobe").chmod(0o755)
                
                return self.is_installed()
            
        except Exception as e:
            print(f"Error installing with Homebrew: {e}")
        
        return False
    
    def _install_windows(self):
        """Install FFmpeg on Windows"""
        print("Downloading FFmpeg for Windows...")
        
        try:
            # Download a Windows build
            ffmpeg_url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-essentials.zip"
            ffmpeg_zip = self.install_dir / "ffmpeg.zip"
            urllib.request.urlretrieve(ffmpeg_url, ffmpeg_zip)
            
            # Extract
            with zipfile.ZipFile(ffmpeg_zip, 'r') as zip_ref:
                zip_ref.extractall(self.install_dir)
            
            # Find the bin directory in the extracted files
            extracted_dirs = [d for d in self.install_dir.iterdir() if d.is_dir() and d.name.startswith('ffmpeg')]
            if extracted_dirs:
                extracted_dir = extracted_dirs[0]
                extracted_bin = extracted_dir / "bin"
                
                # Copy binaries to our bin directory
                ffmpeg_exe = extracted_bin / "ffmpeg.exe"
                ffprobe_exe = extracted_bin / "ffprobe.exe"
                
                if ffmpeg_exe.exists() and ffprobe_exe.exists():
                    shutil.copy(ffmpeg_exe, self.bin_dir)
                    shutil.copy(ffprobe_exe, self.bin_dir)
            
            # Clean up
            ffmpeg_zip.unlink()
            if extracted_dirs:
                shutil.rmtree(extracted_dirs[0])
            
            return self.is_installed()
            
        except Exception as e:
            print(f"Error downloading FFmpeg for Windows: {e}")
            return False
    
    def _install_linux(self):
        """Install FFmpeg on Linux"""
        print("Attempting to install FFmpeg on Linux...")
        
        try:
            # Try apt (Ubuntu/Debian)
            subprocess.run(["sudo", "apt", "update"], check=True)
            subprocess.run(["sudo", "apt", "install", "-y", "ffmpeg"], check=True)
            
            # Find and copy binaries
            result = subprocess.run(["which", "ffmpeg"], 
                                  capture_output=True, 
                                  text=True, 
                                  check=True)
            system_ffmpeg = Path(result.stdout.strip())
            
            result = subprocess.run(["which", "ffprobe"], 
                                  capture_output=True, 
                                  text=True, 
                                  check=True)
            system_ffprobe = Path(result.stdout.strip())
            
            if system_ffmpeg.exists() and system_ffprobe.exists():
                shutil.copy(system_ffmpeg, self.bin_dir)
                shutil.copy(system_ffprobe, self.bin_dir)
                
                return self.is_installed()
                
        except Exception as e:
            print(f"Error installing FFmpeg with apt: {e}")
            
            # Try yum/dnf (CentOS/RHEL/Fedora)
            try:
                # Try dnf first
                subprocess.run(["sudo", "dnf", "install", "-y", "ffmpeg"], check=True)
            except:
                try:
                    # Try yum
                    subprocess.run(["sudo", "yum", "install", "-y", "epel-release"], check=True)
                    subprocess.run(["sudo", "yum", "install", "-y", "ffmpeg"], check=True)
                except Exception as e2:
                    print(f"Error installing FFmpeg with yum/dnf: {e2}")
                    return False
            
            # Try to find and copy binaries
            try:
                result = subprocess.run(["which", "ffmpeg"], 
                                      capture_output=True, 
                                      text=True, 
                                      check=True)
                system_ffmpeg = Path(result.stdout.strip())
                
                result = subprocess.run(["which", "ffprobe"], 
                                      capture_output=True, 
                                      text=True, 
                                      check=True)
                system_ffprobe = Path(result.stdout.strip())
                
                if system_ffmpeg.exists() and system_ffprobe.exists():
                    shutil.copy(system_ffmpeg, self.bin_dir)
                    shutil.copy(system_ffprobe, self.bin_dir)
                    
                    return self.is_installed()
            except Exception as e:
                print(f"Error copying Linux binaries: {e}")
                return False
        
        return False

def install_ffmpeg_if_needed():
    """
    Install FFmpeg if it's not already available
    
    Returns:
        bool: True if FFmpeg is available (either already installed or newly installed)
    """
    installer = FFmpegInstaller()
    
    # Check if already installed in our directory
    if installer.is_installed():
        print("✅ FFmpeg is already installed")
        version = installer.get_ffmpeg_version()
        if version:
            print(f"   FFmpeg version: {version}")
        return True
    
    # Try to install
    print("Installing FFmpeg...")
    if installer.download_and_install():
        print("✅ FFmpeg installed successfully")
        version = installer.get_ffmpeg_version()
        if version:
            print(f"   FFmpeg version: {version}")
        return True
    else:
        print("❌ Failed to install FFmpeg")
        return False

if __name__ == "__main__":
    # Run the installer when executed directly
    install_ffmpeg_if_needed()