"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                         🧹 TEMP FILE CLEANUP REGISTRY                        ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import shutil
import atexit

# ═══════════════════════════════════════════════════════════════════════════════
#                         🗂️ TEMP DIRECTORY REGISTRY
# ═══════════════════════════════════════════════════════════════════════════════

# Global list to track temporary directories
temp_directories = []


def register_temp_directory(temp_dir: str):
    """
    Register a temporary directory for cleanup on exit.
    
    Args:
        temp_dir: Path to temporary directory
    """
    if temp_dir and temp_dir not in temp_directories:
        temp_directories.append(temp_dir)


def unregister_temp_directory(temp_dir: str):
    """
    Remove a temporary directory from cleanup registry.
    Call this after manually cleaning up a directory.
    
    Args:
        temp_dir: Path to temporary directory
    """
    if temp_dir in temp_directories:
        temp_directories.remove(temp_dir)


def cleanup_temp_directories():
    """
    Clean up all registered temp directories.
    Called automatically on program exit via atexit.
    """
    global temp_directories
    
    cleaned = 0
    failed = 0
    
    for temp_dir in temp_directories:
        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
                cleaned += 1
        except Exception as e:
            failed += 1
            pass
    
    if cleaned > 0 or failed > 0:
        print(f"🧹 Cleanup: {cleaned} temp directories removed, {failed} failed")
    
    temp_directories.clear()


def cleanup_single_directory(temp_dir: str, unregister: bool = True):
    """
    Clean up a single temporary directory immediately.
    
    Args:
        temp_dir: Path to temporary directory
        unregister: Whether to remove from registry (default: True)
    
    Returns:
        bool: True if cleanup successful, False otherwise
    """
    try:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
        
        if unregister:
            unregister_temp_directory(temp_dir)
        
        return True
    except Exception as e:
        print(f"⚠️ Failed to cleanup {temp_dir}: {e}")
        return False


# ═══════════════════════════════════════════════════════════════════════════════
#                         🔄 REGISTER ATEXIT HANDLER
# ═══════════════════════════════════════════════════════════════════════════════

# Automatically cleanup all temp directories when program exits
atexit.register(cleanup_temp_directories)