"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  ⬡ USER GESTURES MODULE V3.0 — HOLOGRAM EDITION ⬡                           ║
║  Gesture Data Management • JSON Storage • Trash System                      ║
║  Backup & Restore • Import/Export Functionality                             ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import json
import os
import time
import shutil
from datetime import datetime


# ═══════════════════════════════════════════════════════════════════════════════
# ⬡ FILE PATHS
# ═══════════════════════════════════════════════════════════════════════════════

GESTURE_FILE = "gestures.json"
TRASH_FILE = "gestures_trash.json"


# ═══════════════════════════════════════════════════════════════════════════════
# ⬡ HOLOGRAM CONSOLE LOGGER
# ═══════════════════════════════════════════════════════════════════════════════

class HoloLogger:
    """Cyberpunk-styled console logger."""
    
    # ANSI Color codes for terminal
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    MAGENTA = '\033[95m'
    BLUE = '\033[94m'
    WHITE = '\033[97m'
    DIM = '\033[2m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    @staticmethod
    def _timestamp():
        return datetime.now().strftime("%H:%M:%S")
    
    @classmethod
    def info(cls, message):
        print(f"{cls.DIM}[{cls._timestamp()}]{cls.RESET} {cls.CYAN}⬡{cls.RESET} {cls.WHITE}{message}{cls.RESET}")
    
    @classmethod
    def success(cls, message):
        print(f"{cls.DIM}[{cls._timestamp()}]{cls.RESET} {cls.GREEN}✓{cls.RESET} {cls.GREEN}{message}{cls.RESET}")
    
    @classmethod
    def warning(cls, message):
        print(f"{cls.DIM}[{cls._timestamp()}]{cls.RESET} {cls.YELLOW}⚠{cls.RESET} {cls.YELLOW}{message}{cls.RESET}")
    
    @classmethod
    def error(cls, message):
        print(f"{cls.DIM}[{cls._timestamp()}]{cls.RESET} {cls.RED}✖{cls.RESET} {cls.RED}{message}{cls.RESET}")
    
    @classmethod
    def trash(cls, message):
        print(f"{cls.DIM}[{cls._timestamp()}]{cls.RESET} {cls.MAGENTA}🗑️{cls.RESET} {cls.MAGENTA}{message}{cls.RESET}")
    
    @classmethod
    def restore(cls, message):
        print(f"{cls.DIM}[{cls._timestamp()}]{cls.RESET} {cls.CYAN}♻️{cls.RESET} {cls.CYAN}{message}{cls.RESET}")
    
    @classmethod
    def save(cls, message):
        print(f"{cls.DIM}[{cls._timestamp()}]{cls.RESET} {cls.BLUE}💾{cls.RESET} {cls.BLUE}{message}{cls.RESET}")
    
    @classmethod
    def load(cls, message):
        print(f"{cls.DIM}[{cls._timestamp()}]{cls.RESET} {cls.CYAN}📂{cls.RESET} {cls.WHITE}{message}{cls.RESET}")


# Create logger instance
log = HoloLogger()


# ═══════════════════════════════════════════════════════════════════════════════
# ⬡ CORE GESTURE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def load_gestures():
    """Load all saved gestures from JSON file."""
    if not os.path.exists(GESTURE_FILE):
        log.info(f"No gesture file found. Starting fresh.")
        return []
    try:
        with open(GESTURE_FILE, "r") as f:
            gestures = json.load(f)
            log.load(f"Loaded {len(gestures)} gesture(s) from database")
            return gestures
    except json.JSONDecodeError as e:
        log.error(f"JSON parse error: {e}")
        return []
    except Exception as e:
        log.error(f"Failed to load gestures: {e}")
        return []


def save_gesture(gesture):
    """Save a new gesture to the database."""
    gestures = load_gestures()
    gestures.append(gesture)
    
    try:
        with open(GESTURE_FILE, "w") as f:
            json.dump(gestures, f, indent=2)
        log.save(f"Gesture saved: {gesture['name']} [ID: {gesture.get('id', 'N/A')}]")
        return True
    except Exception as e:
        log.error(f"Failed to save gesture: {e}")
        return False


def update_gesture(updated_gesture):
    """Update an existing gesture in the database."""
    gestures = load_gestures()
    
    found = False
    for i, gesture in enumerate(gestures):
        if gesture['id'] == updated_gesture['id']:
            gestures[i] = updated_gesture
            found = True
            break
    
    if not found:
        log.warning(f"Gesture not found for update: {updated_gesture.get('id')}")
        return False
    
    try:
        with open(GESTURE_FILE, 'w') as f:
            json.dump(gestures, f, indent=2)
        log.success(f"Gesture updated: {updated_gesture['name']}")
        return True
    except Exception as e:
        log.error(f"Failed to update gesture: {e}")
        return False


def find_gesture_by_id(gesture_id):
    """Find a gesture by its unique ID."""
    gestures = load_gestures()
    for gesture in gestures:
        if gesture['id'] == gesture_id:
            return gesture
    log.warning(f"Gesture not found: {gesture_id}")
    return None


def get_gesture_count():
    """Get total number of saved gestures."""
    return len(load_gestures())


def get_active_gestures(mode=None):
    """Get all enabled gestures, optionally filtered by mode."""
    gestures = load_gestures()
    active = [g for g in gestures if g.get('enabled', True)]
    
    if mode:
        active = [g for g in active if g.get('mode') in [mode, 'ALL']]
        log.info(f"Found {len(active)} active gesture(s) for mode: {mode}")
    else:
        log.info(f"Found {len(active)} active gesture(s)")
    
    return active


def toggle_gesture(gesture_id):
    """Toggle a gesture's enabled/disabled status."""
    gesture = find_gesture_by_id(gesture_id)
    if gesture:
        gesture['enabled'] = not gesture.get('enabled', True)
        update_gesture(gesture)
        status = "ENABLED" if gesture['enabled'] else "DISABLED"
        log.info(f"Gesture {status}: {gesture['name']}")
        return gesture['enabled']
    return False


# ═══════════════════════════════════════════════════════════════════════════════
# ⬡ TRASH SYSTEM FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def load_trash():
    """Load deleted gestures from trash file."""
    if not os.path.exists(TRASH_FILE):
        return []
    try:
        with open(TRASH_FILE, "r") as f:
            trash = json.load(f)
            return trash
    except json.JSONDecodeError:
        log.error("Trash file corrupted. Resetting...")
        return []
    except Exception as e:
        log.error(f"Failed to load trash: {e}")
        return []


def get_trash_count():
    """Get number of gestures in trash."""
    return len(load_trash())


def delete_gesture(gesture_id):
    """Move a gesture to trash (soft delete)."""
    gestures = load_gestures()
    trash = load_trash()
    
    # Find and move to trash
    deleted_gesture = None
    for i, g in enumerate(gestures):
        if g.get("id") == gesture_id:
            deleted_gesture = gestures.pop(i)
            deleted_gesture['deleted_at'] = time.strftime("%Y-%m-%d %H:%M:%S")
            break
    
    if deleted_gesture:
        trash.append(deleted_gesture)
        
        try:
            # Save both files
            with open(GESTURE_FILE, "w") as f:
                json.dump(gestures, f, indent=2)
            with open(TRASH_FILE, "w") as f:
                json.dump(trash, f, indent=2)
            
            log.trash(f"Moved to trash: {deleted_gesture['name']}")
            return True
        except Exception as e:
            log.error(f"Failed to delete gesture: {e}")
            return False
    
    log.warning(f"Gesture not found for deletion: {gesture_id}")
    return False


def restore_gesture(gesture_id):
    """Restore a gesture from trash to active gestures."""
    trash = load_trash()
    gestures = load_gestures()
    
    # Find in trash
    restored_gesture = None
    for i, g in enumerate(trash):
        if g.get("id") == gesture_id:
            restored_gesture = trash.pop(i)
            break
    
    if restored_gesture:
        # Remove deleted_at timestamp
        if 'deleted_at' in restored_gesture:
            del restored_gesture['deleted_at']
        
        gestures.append(restored_gesture)
        
        try:
            # Save both files
            with open(GESTURE_FILE, "w") as f:
                json.dump(gestures, f, indent=2)
            with open(TRASH_FILE, "w") as f:
                json.dump(trash, f, indent=2)
            
            log.restore(f"Restored from trash: {restored_gesture['name']}")
            return True
        except Exception as e:
            log.error(f"Failed to restore gesture: {e}")
            return False
    
    log.warning(f"Gesture not found in trash: {gesture_id}")
    return False


def permanent_delete_gesture(gesture_id):
    """Permanently delete a gesture from trash (cannot be undone)."""
    trash = load_trash()
    
    original_count = len(trash)
    trash = [g for g in trash if g.get("id") != gesture_id]
    
    if len(trash) == original_count:
        log.warning(f"Gesture not found in trash: {gesture_id}")
        return False
    
    try:
        with open(TRASH_FILE, "w") as f:
            json.dump(trash, f, indent=2)
        log.trash(f"Permanently deleted: {gesture_id}")
        return True
    except Exception as e:
        log.error(f"Failed to permanently delete: {e}")
        return False


def empty_trash():
    """Permanently delete all gestures in trash."""
    trash = load_trash()
    count = len(trash)
    
    if count == 0:
        log.info("Trash is already empty")
        return True
    
    try:
        with open(TRASH_FILE, 'w') as f:
            json.dump([], f)
        log.trash(f"Trash emptied: {count} gesture(s) permanently deleted")
        return True
    except Exception as e:
        log.error(f"Failed to empty trash: {e}")
        return False


def clear_all_gestures():
    """Move all gestures to trash (bulk soft delete)."""
    gestures = load_gestures()
    
    if not gestures:
        log.info("No gestures to clear")
        return True
    
    trash = load_trash()
    
    # Add deleted_at timestamp to all
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    for g in gestures:
        g['deleted_at'] = timestamp
        trash.append(g)
    
    try:
        # Clear gestures and update trash
        with open(GESTURE_FILE, 'w') as f:
            json.dump([], f)
        with open(TRASH_FILE, 'w') as f:
            json.dump(trash, f, indent=2)
        
        log.trash(f"All {len(gestures)} gesture(s) moved to trash")
        return True
    except Exception as e:
        log.error(f"Failed to clear gestures: {e}")
        return False


# ═══════════════════════════════════════════════════════════════════════════════
# ⬡ BACKUP & IMPORT FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def backup_gestures(backup_path=None):
    """Create a backup of all gestures."""
    if not os.path.exists(GESTURE_FILE):
        log.warning("No gesture file to backup")
        return None
    
    if backup_path is None:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_path = f"gestures_backup_{timestamp}.json"
    
    try:
        shutil.copy(GESTURE_FILE, backup_path)
        log.save(f"Backup created: {backup_path}")
        return backup_path
    except Exception as e:
        log.error(f"Failed to create backup: {e}")
        return None


def import_gestures(import_path):
    """Import gestures from a backup file."""
    if not os.path.exists(import_path):
        log.error(f"Import file not found: {import_path}")
        return 0
    
    try:
        with open(import_path, 'r') as f:
            imported = json.load(f)
        
        if not isinstance(imported, list):
            log.error("Invalid import file format")
            return 0
        
        current = load_gestures()
        
        # Merge, avoiding duplicates by ID
        existing_ids = {g['id'] for g in current}
        new_gestures = [g for g in imported if g.get('id') not in existing_ids]
        
        if not new_gestures:
            log.info("No new gestures to import (all duplicates)")
            return 0
        
        current.extend(new_gestures)
        
        with open(GESTURE_FILE, 'w') as f:
            json.dump(current, f, indent=2)
        
        log.success(f"Imported {len(new_gestures)} new gesture(s)")
        return len(new_gestures)
    
    except json.JSONDecodeError:
        log.error("Invalid JSON in import file")
        return 0
    except Exception as e:
        log.error(f"Failed to import gestures: {e}")
        return 0


def export_gestures(export_path=None):
    """Export all gestures to a file."""
    gestures = load_gestures()
    
    if not gestures:
        log.warning("No gestures to export")
        return None
    
    if export_path is None:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        export_path = f"gestures_export_{timestamp}.json"
    
    try:
        with open(export_path, 'w') as f:
            json.dump(gestures, f, indent=2)
        log.save(f"Exported {len(gestures)} gesture(s) to: {export_path}")
        return export_path
    except Exception as e:
        log.error(f"Failed to export gestures: {e}")
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# ⬡ STATISTICS FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def get_gesture_stats():
    """Get comprehensive gesture statistics."""
    gestures = load_gestures()
    trash = load_trash()
    
    stats = {
        'total': len(gestures),
        'enabled': sum(1 for g in gestures if g.get('enabled', True)),
        'disabled': sum(1 for g in gestures if not g.get('enabled', True)),
        'in_trash': len(trash),
        'by_mode': {},
        'by_action': {}
    }
    
    # Count by mode
    for g in gestures:
        mode = g.get('mode', 'ALL')
        stats['by_mode'][mode] = stats['by_mode'].get(mode, 0) + 1
    
    # Count by action type
    for g in gestures:
        action_type = g.get('action', {}).get('type', 'UNKNOWN')
        stats['by_action'][action_type] = stats['by_action'].get(action_type, 0) + 1
    
    return stats


def print_stats():
    """Print formatted gesture statistics to console."""
    stats = get_gesture_stats()
    
    print(f"""
╔══════════════════════════════════════════════════════════════════╗
║  ⬡ GESTURE DATABASE STATISTICS                                  ║
╠══════════════════════════════════════════════════════════════════╣
║  ▸ Total Gestures:    {stats['total']:>5}                                    ║
║  ▸ Enabled:           {stats['enabled']:>5}                                    ║
║  ▸ Disabled:          {stats['disabled']:>5}                                    ║
║  ▸ In Trash:          {stats['in_trash']:>5}                                    ║
╠══════════════════════════════════════════════════════════════════╣
║  BY MODE:                                                        ║""")
    
    for mode, count in stats['by_mode'].items():
        print(f"║  ▸ {mode:<18} {count:>5}                                    ║")
    
    print(f"""╠══════════════════════════════════════════════════════════════════╣
║  BY ACTION TYPE:                                                 ║""")
    
    for action, count in stats['by_action'].items():
        print(f"║  ▸ {action:<18} {count:>5}                                    ║")
    
    print("╚══════════════════════════════════════════════════════════════════╝")


# ═══════════════════════════════════════════════════════════════════════════════
# ⬡ MODULE INFO
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║  ⬡ USER GESTURES MODULE V3.0 — HOLOGRAM EDITION ⬡                           ║
║  Gesture Data Management • JSON Storage • Trash System                      ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  CORE FUNCTIONS:                                                            ║
║  ▸ load_gestures()      - Load all saved gestures                           ║
║  ▸ save_gesture()       - Save a new gesture                                ║
║  ▸ update_gesture()     - Update existing gesture                           ║
║  ▸ delete_gesture()     - Move gesture to trash                             ║
║  ▸ toggle_gesture()     - Enable/disable gesture                            ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  TRASH FUNCTIONS:                                                           ║
║  ▸ load_trash()         - Load trashed gestures                             ║
║  ▸ restore_gesture()    - Restore from trash                                ║
║  ▸ permanent_delete()   - Delete forever                                    ║
║  ▸ empty_trash()        - Clear all trash                                   ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  BACKUP FUNCTIONS:                                                          ║
║  ▸ backup_gestures()    - Create backup file                                ║
║  ▸ import_gestures()    - Import from backup                                ║
║  ▸ export_gestures()    - Export to file                                    ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Print current stats
    print_stats()