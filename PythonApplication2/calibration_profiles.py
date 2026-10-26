"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  ⬡ CALIBRATION PROFILES MODULE V3.0 — HOLOGRAM EDITION ⬡                   ║
║  Save/Load Multiple Calibration Profiles • Hologram Mode Support            ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import json
import os
from datetime import datetime
from dataclasses import dataclass, asdict, field
from typing import List, Optional, Dict, Tuple
from pathlib import Path


@dataclass
class CalibrationData:
    """Calibration boundary data with hologram support"""
    margin_x_min: float = 100
    margin_x_max: float = 540
    margin_y_min: float = 100
    margin_y_max: float = 380
    captured_points: List[tuple] = field(default_factory=list)
    accuracy_score: float = 0.0
    camera_index: int = 0
    hologram_mode: bool = False  # ⬡ HOLOGRAM MODE FLAG
    
    # ⬡ Hologram visual settings
    neon_color: Tuple[int, int, int] = (0, 255, 255)  # Cyan default
    glow_intensity: float = 1.0
    scan_line_speed: float = 1.0
    particle_density: int = 50
    grid_enabled: bool = True
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'margin_x_min': self.margin_x_min,
            'margin_x_max': self.margin_x_max,
            'margin_y_min': self.margin_y_min,
            'margin_y_max': self.margin_y_max,
            'captured_points': self.captured_points,
            'accuracy_score': self.accuracy_score,
            'camera_index': self.camera_index,
            'hologram_mode': self.hologram_mode,
            'neon_color': list(self.neon_color),
            'glow_intensity': self.glow_intensity,
            'scan_line_speed': self.scan_line_speed,
            'particle_density': self.particle_density,
            'grid_enabled': self.grid_enabled
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'CalibrationData':
        """Create from dictionary"""
        neon_color = data.get('neon_color', [0, 255, 255])
        return cls(
            margin_x_min=data.get('margin_x_min', 100),
            margin_x_max=data.get('margin_x_max', 540),
            margin_y_min=data.get('margin_y_min', 100),
            margin_y_max=data.get('margin_y_max', 380),
            captured_points=[tuple(p) for p in data.get('captured_points', [])],
            accuracy_score=data.get('accuracy_score', 0.0),
            camera_index=data.get('camera_index', 0),
            hologram_mode=data.get('hologram_mode', False),
            neon_color=tuple(neon_color),
            glow_intensity=data.get('glow_intensity', 1.0),
            scan_line_speed=data.get('scan_line_speed', 1.0),
            particle_density=data.get('particle_density', 50),
            grid_enabled=data.get('grid_enabled', True)
        )


@dataclass
class CalibrationProfile:
    """A named calibration profile with metadata"""
    name: str
    description: str = ""
    calibration: CalibrationData = field(default_factory=CalibrationData)
    created_at: str = ""
    updated_at: str = ""
    use_count: int = 0
    is_favorite: bool = False
    icon: str = "👤"
    tags: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at
    
    @property
    def display_name(self) -> str:
        """Get display name with hologram indicator"""
        hologram_badge = " ⬡" if self.calibration.hologram_mode else ""
        favorite_badge = " ⭐" if self.is_favorite else ""
        return f"{self.icon} {self.name}{hologram_badge}{favorite_badge}"
    
    @property
    def is_hologram(self) -> bool:
        """Quick check if profile uses hologram mode"""
        return self.calibration.hologram_mode
    
    def get_age_str(self) -> str:
        """Get human-readable age"""
        try:
            created = datetime.fromisoformat(self.created_at)
            delta = datetime.now() - created
            
            if delta.days > 365:
                return f"{delta.days // 365} year(s) ago"
            elif delta.days > 30:
                return f"{delta.days // 30} month(s) ago"
            elif delta.days > 0:
                return f"{delta.days} day(s) ago"
            elif delta.seconds > 3600:
                return f"{delta.seconds // 3600} hour(s) ago"
            else:
                return "Recently"
        except:
            return "Unknown"
            
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'name': self.name,
            'description': self.description,
            'calibration': self.calibration.to_dict(),
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'use_count': self.use_count,
            'is_favorite': self.is_favorite,
            'icon': self.icon,
            'tags': self.tags
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'CalibrationProfile':
        """Create from dictionary"""
        cal_data = data.get('calibration', {})
        return cls(
            name=data.get('name', 'Unnamed'),
            description=data.get('description', ''),
            calibration=CalibrationData.from_dict(cal_data),
            created_at=data.get('created_at', ''),
            updated_at=data.get('updated_at', ''),
            use_count=data.get('use_count', 0),
            is_favorite=data.get('is_favorite', False),
            icon=data.get('icon', '👤'),
            tags=data.get('tags', [])
        )


class ProfileManager:
    """
    ╔══════════════════════════════════════════════════════════════════╗
    ║  ⬡ PROFILE MANAGER - Manage Calibration Profiles ⬡             ║
    ╚══════════════════════════════════════════════════════════════════╝
    """
    
    # Preset profile templates
    PRESET_PROFILES = {
        "sitting": {
            "icon": "🪑", 
            "description": "Standard sitting position at desk",
            "tags": ["posture", "default"]
        },
        "standing": {
            "icon": "🧍", 
            "description": "Standing at desk position",
            "tags": ["posture", "standing"]
        },
        "left_hand": {
            "icon": "🤚", 
            "description": "Optimized for left hand tracking",
            "tags": ["hand", "left"]
        },
        "right_hand": {
            "icon": "✋", 
            "description": "Optimized for right hand tracking",
            "tags": ["hand", "right"]
        },
        "close_range": {
            "icon": "📱", 
            "description": "Close to camera (< 1 meter)",
            "tags": ["distance", "close"]
        },
        "far_range": {
            "icon": "🖥️", 
            "description": "Far from camera (> 1 meter)",
            "tags": ["distance", "far"]
        },
        "hologram": {
            "icon": "⬡", 
            "description": "Cyberpunk hologram mode with neon effects",
            "tags": ["visual", "hologram", "cyberpunk"]
        },
        "hologram_purple": {
            "icon": "⬡", 
            "description": "Purple neon hologram theme",
            "tags": ["visual", "hologram", "purple"]
        },
        "hologram_green": {
            "icon": "⬡", 
            "description": "Matrix-style green hologram",
            "tags": ["visual", "hologram", "green", "matrix"]
        },
    }
    
    # Preset hologram color schemes
    HOLOGRAM_THEMES = {
        "cyan": (0, 255, 255),
        "purple": (255, 0, 255),
        "green": (0, 255, 0),
        "blue": (0, 100, 255),
        "red": (255, 50, 50),
        "orange": (255, 165, 0),
        "pink": (255, 105, 180),
    }
    
    def __init__(self, profiles_dir: str = None):
        """Initialize profile manager"""
        if profiles_dir:
            self.profiles_dir = Path(profiles_dir)
        else:
            self.profiles_dir = Path.home() / ".gesture_control" / "calibration_profiles"
            
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        self.profiles: Dict[str, CalibrationProfile] = {}
        self.active_profile: Optional[str] = None
        self._load_all_profiles()
        
    def _load_all_profiles(self):
        """Load all profiles from disk"""
        self.profiles.clear()
        
        for file_path in self.profiles_dir.glob("*.json"):
            if file_path.name.startswith("_"):
                continue
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    profile = CalibrationProfile.from_dict(data)
                    self.profiles[profile.name] = profile
            except Exception as e:
                print(f"⚠️ Error loading profile {file_path}: {e}")
                
        # Load active profile
        active_file = self.profiles_dir / "_active.txt"
        if active_file.exists():
            try:
                name = active_file.read_text().strip()
                if name in self.profiles:
                    self.active_profile = name
            except:
                pass
        
        hologram_count = len([p for p in self.profiles.values() if p.is_hologram])
        print(f"📂 Loaded {len(self.profiles)} profiles ({hologram_count} ⬡ hologram)")
        
    def _get_filename(self, name: str) -> str:
        """Generate safe filename from profile name"""
        safe = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in name)
        return safe.lower().replace(' ', '_')
        
    def save_profile(self, profile: CalibrationProfile) -> bool:
        """Save profile to disk"""
        profile.updated_at = datetime.now().isoformat()
        
        filename = self._get_filename(profile.name) + ".json"
        file_path = self.profiles_dir / filename
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(profile.to_dict(), f, indent=2, ensure_ascii=False)
                
            self.profiles[profile.name] = profile
            hologram_status = "⬡ HOLOGRAM" if profile.calibration.hologram_mode else "STANDARD"
            print(f"💾 Profile saved: {profile.name} [{hologram_status}]")
            return True
        except Exception as e:
            print(f"❌ Error saving profile: {e}")
            return False
            
    def create_profile(self, name: str, calibration_data: CalibrationData = None,
                      description: str = "", icon: str = "👤", 
                      hologram_mode: bool = False,
                      tags: List[str] = None) -> Optional[CalibrationProfile]:
        """Create a new profile"""
        if name in self.profiles:
            # Update existing
            profile = self.profiles[name]
            if calibration_data:
                profile.calibration = calibration_data
            profile.description = description or profile.description
            profile.icon = icon
            if tags:
                profile.tags = tags
        else:
            cal_data = calibration_data or CalibrationData()
            cal_data.hologram_mode = hologram_mode
            
            profile = CalibrationProfile(
                name=name,
                description=description,
                calibration=cal_data,
                icon=icon,
                tags=tags or []
            )
        
        if self.save_profile(profile):
            return profile
        return None
    
    def create_hologram_profile(self, name: str, 
                               calibration_data: CalibrationData = None,
                               theme: str = "cyan") -> Optional[CalibrationProfile]:
        """⬡ Quick create hologram profile with theme"""
        cal_data = calibration_data or CalibrationData()
        cal_data.hologram_mode = True
        cal_data.neon_color = self.HOLOGRAM_THEMES.get(theme, self.HOLOGRAM_THEMES["cyan"])
        
        return self.create_profile(
            name=name,
            calibration_data=cal_data,
            description=f"Hologram mode - {theme.title()} theme",
            icon="⬡",
            hologram_mode=True,
            tags=["hologram", theme, "cyberpunk"]
        )
    
    def delete_profile(self, name: str) -> bool:
        """Delete a profile"""
        if name not in self.profiles:
            print(f"❌ Profile not found: {name}")
            return False
            
        filename = self._get_filename(name) + ".json"
        file_path = self.profiles_dir / filename
        
        try:
            if file_path.exists():
                file_path.unlink()
                
            del self.profiles[name]
            
            if self.active_profile == name:
                self.active_profile = None
                self._save_active()
                
            print(f"🗑️ Deleted profile: {name}")
            return True
        except Exception as e:
            print(f"❌ Error deleting profile: {e}")
            return False
    
    def _save_active(self):
        """Save active profile setting"""
        active_file = self.profiles_dir / "_active.txt"
        try:
            if self.active_profile:
                active_file.write_text(self.active_profile)
            elif active_file.exists():
                active_file.unlink()
        except:
            pass
    
    def set_active(self, name: str) -> bool:
        """Set active profile"""
        if name not in self.profiles:
            print(f"❌ Profile not found: {name}")
            return False
            
        self.active_profile = name
        self.profiles[name].use_count += 1
        self.save_profile(self.profiles[name])
        self._save_active()
        
        profile = self.profiles[name]
        mode = "⬡ HOLOGRAM MODE" if profile.calibration.hologram_mode else "STANDARD MODE"
        print(f"✅ Active profile: {name} [{mode}]")
        return True
    
    def get_active(self) -> Optional[CalibrationProfile]:
        """Get active profile"""
        if self.active_profile and self.active_profile in self.profiles:
            return self.profiles[self.active_profile]
        return None
    
    def get_active_calibration(self) -> Optional[CalibrationData]:
        """Get active calibration data"""
        profile = self.get_active()
        return profile.calibration if profile else None
    
    def get_all_profiles(self) -> List[CalibrationProfile]:
        """Get all profiles sorted by favorites and use count"""
        return sorted(
            self.profiles.values(),
            key=lambda p: (-int(p.is_favorite), -p.use_count, p.name)
        )
    
    def get_hologram_profiles(self) -> List[CalibrationProfile]:
        """⬡ Get only hologram mode profiles"""
        return [p for p in self.get_all_profiles() if p.calibration.hologram_mode]
    
    def get_standard_profiles(self) -> List[CalibrationProfile]:
        """Get only standard mode profiles"""
        return [p for p in self.get_all_profiles() if not p.calibration.hologram_mode]
    
    def get_profiles_by_tag(self, tag: str) -> List[CalibrationProfile]:
        """Get profiles with specific tag"""
        return [p for p in self.get_all_profiles() if tag in p.tags]
    
    def toggle_favorite(self, name: str) -> bool:
        """Toggle favorite status"""
        if name in self.profiles:
            self.profiles[name].is_favorite = not self.profiles[name].is_favorite
            status = "⭐" if self.profiles[name].is_favorite else "removed from favorites"
            print(f"{'⭐' if self.profiles[name].is_favorite else '☆'} {name}")
            return self.save_profile(self.profiles[name])
        return False
    
    def toggle_hologram_mode(self, name: str) -> bool:
        """⬡ Toggle hologram mode for a profile"""
        if name in self.profiles:
            profile = self.profiles[name]
            profile.calibration.hologram_mode = not profile.calibration.hologram_mode
            
            # Update icon if toggling to hologram
            if profile.calibration.hologram_mode:
                if profile.icon != "⬡":
                    profile.icon = "⬡"
                if "hologram" not in profile.tags:
                    profile.tags.append("hologram")
            else:
                if profile.icon == "⬡":
                    profile.icon = "👤"
                if "hologram" in profile.tags:
                    profile.tags.remove("hologram")
            
            status = "⬡ ENABLED" if profile.calibration.hologram_mode else "DISABLED"
            print(f"⬡ Hologram mode {status} for: {name}")
            return self.save_profile(profile)
        return False
    
    def update_hologram_settings(self, name: str, 
                                 neon_color: Tuple[int, int, int] = None,
                                 glow_intensity: float = None,
                                 scan_line_speed: float = None,
                                 particle_density: int = None,
                                 grid_enabled: bool = None) -> bool:
        """⬡ Update hologram visual settings"""
        if name not in self.profiles:
            return False
        
        profile = self.profiles[name]
        cal = profile.calibration
        
        if neon_color is not None:
            cal.neon_color = neon_color
        if glow_intensity is not None:
            cal.glow_intensity = max(0.0, min(2.0, glow_intensity))
        if scan_line_speed is not None:
            cal.scan_line_speed = max(0.1, min(5.0, scan_line_speed))
        if particle_density is not None:
            cal.particle_density = max(0, min(200, particle_density))
        if grid_enabled is not None:
            cal.grid_enabled = grid_enabled
        
        return self.save_profile(profile)
    
    def export_profile(self, name: str, export_path: str) -> bool:
        """Export profile to file"""
        if name not in self.profiles:
            print(f"❌ Profile not found: {name}")
            return False
            
        profile = self.profiles[name]
        data = profile.to_dict()
        data['_exported_at'] = datetime.now().isoformat()
        data['_version'] = "3.0_hologram"
        data['_export_source'] = "ProfileManager"
        
        try:
            export_file = Path(export_path)
            export_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"📤 Exported profile to: {export_path}")
            return True
        except Exception as e:
            print(f"❌ Export error: {e}")
            return False
    
    def import_profile(self, import_path: str, new_name: str = None) -> Optional[CalibrationProfile]:
        """Import profile from file"""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Remove metadata
            data.pop('_exported_at', None)
            data.pop('_version', None)
            data.pop('_export_source', None)
            
            profile = CalibrationProfile.from_dict(data)
            
            # Use new name if provided
            if new_name:
                profile.name = new_name
            
            # Ensure unique name
            original = profile.name
            counter = 1
            while profile.name in self.profiles:
                profile.name = f"{original} ({counter})"
                counter += 1
                
            if self.save_profile(profile):
                mode = "⬡ HOLOGRAM" if profile.calibration.hologram_mode else "STANDARD"
                print(f"📥 Imported profile: {profile.name} [{mode}]")
                return profile
            return None
            
        except Exception as e:
            print(f"❌ Import error: {e}")
            return None
    
    def export_all_profiles(self, export_dir: str) -> int:
        """Export all profiles to directory"""
        export_path = Path(export_dir)
        export_path.mkdir(parents=True, exist_ok=True)
        
        count = 0
        for profile in self.profiles.values():
            filename = self._get_filename(profile.name) + ".json"
            file_path = export_path / filename
            if self.export_profile(profile.name, str(file_path)):
                count += 1
        
        print(f"📤 Exported {count}/{len(self.profiles)} profiles to: {export_dir}")
        return count
    
    def import_all_profiles(self, import_dir: str) -> int:
        """Import all profiles from directory"""
        import_path = Path(import_dir)
        if not import_path.exists():
            print(f"❌ Directory not found: {import_dir}")
            return 0
        
        count = 0
        for file_path in import_path.glob("*.json"):
            if file_path.name.startswith("_"):
                continue
            if self.import_profile(str(file_path)):
                count += 1
        
        print(f"📥 Imported {count} profiles from: {import_dir}")
        return count
    
    def duplicate_profile(self, name: str, new_name: str = None) -> Optional[CalibrationProfile]:
        """Duplicate an existing profile"""
        if name not in self.profiles:
            print(f"❌ Profile not found: {name}")
            return None
        
        original = self.profiles[name]
        
        # Generate new name
        if not new_name:
            counter = 1
            new_name = f"{name} (Copy)"
            while new_name in self.profiles:
                counter += 1
                new_name = f"{name} (Copy {counter})"
        
        # Create duplicate
        new_profile = CalibrationProfile(
            name=new_name,
            description=original.description,
            calibration=CalibrationData.from_dict(original.calibration.to_dict()),
            icon=original.icon,
            tags=original.tags.copy()
        )
        
        if self.save_profile(new_profile):
            print(f"📋 Duplicated: {name} → {new_name}")
            return new_profile
        return None
    
    def rename_profile(self, old_name: str, new_name: str) -> bool:
        """Rename a profile"""
        if old_name not in self.profiles:
            print(f"❌ Profile not found: {old_name}")
            return False
        
        if new_name in self.profiles:
            print(f"❌ Profile name already exists: {new_name}")
            return False
        
        # Get profile and delete old file
        profile = self.profiles[old_name]
        old_filename = self._get_filename(old_name) + ".json"
        old_path = self.profiles_dir / old_filename
        
        if old_path.exists():
            old_path.unlink()
        
        # Update name and save
        del self.profiles[old_name]
        profile.name = new_name
        
        if self.save_profile(profile):
            # Update active if needed
            if self.active_profile == old_name:
                self.active_profile = new_name
                self._save_active()
            
            print(f"✏️ Renamed: {old_name} → {new_name}")
            return True
        return False
    
    def get_profile_count(self) -> int:
        """Get number of profiles"""
        return len(self.profiles)
    
    def get_stats(self) -> dict:
        """⬡ Get detailed profile statistics"""
        total = len(self.profiles)
        hologram = len(self.get_hologram_profiles())
        standard = len(self.get_standard_profiles())
        favorites = sum(1 for p in self.profiles.values() if p.is_favorite)
        
        # Most used profile
        most_used = max(self.profiles.values(), key=lambda p: p.use_count) if self.profiles else None
        
        # Tag statistics
        all_tags = []
        for p in self.profiles.values():
            all_tags.extend(p.tags)
        
        tag_counts = {}
        for tag in all_tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        return {
            'total': total,
            'hologram': hologram,
            'standard': standard,
            'favorites': favorites,
            'active': self.active_profile,
            'most_used': most_used.name if most_used else None,
            'most_used_count': most_used.use_count if most_used else 0,
            'tag_counts': tag_counts,
            'storage_path': str(self.profiles_dir)
        }
    
    def print_stats(self):
        """Print formatted statistics"""
        stats = self.get_stats()
        
        print("\n" + "="*60)
        print("⬡ CALIBRATION PROFILE STATISTICS")
        print("="*60)
        print(f"Total Profiles:     {stats['total']}")
        print(f"⬡ Hologram Mode:    {stats['hologram']}")
        print(f"  Standard Mode:    {stats['standard']}")
        print(f"⭐ Favorites:       {stats['favorites']}")
        print(f"Active Profile:     {stats['active'] or 'None'}")
        print(f"Most Used:          {stats['most_used']} ({stats['most_used_count']} times)")
        print(f"Storage Location:   {stats['storage_path']}")
        
        if stats['tag_counts']:
            print("\nTag Distribution:")
            for tag, count in sorted(stats['tag_counts'].items(), key=lambda x: -x[1]):
                print(f"  #{tag}: {count}")
        
        print("="*60 + "\n")
    
    def list_profiles(self, filter_hologram: bool = None, filter_favorite: bool = None):
        """Print formatted list of profiles"""
        profiles = self.get_all_profiles()
        
        if filter_hologram is not None:
            profiles = [p for p in profiles if p.is_hologram == filter_hologram]
        
        if filter_favorite:
            profiles = [p for p in profiles if p.is_favorite]
        
        if not profiles:
            print("No profiles found.")
            return
        
        print("\n" + "="*80)
        print("⬡ CALIBRATION PROFILES")
        print("="*80)
        
        for i, profile in enumerate(profiles, 1):
            active_marker = "→" if profile.name == self.active_profile else " "
            mode = "⬡" if profile.is_hologram else "○"
            fav = "⭐" if profile.is_favorite else "  "
            
            print(f"{active_marker} {i:2d}. {fav} {mode} {profile.icon} {profile.name}")
            print(f"       {profile.description}")
            print(f"       Used: {profile.use_count} times | {profile.get_age_str()}")
            
            if profile.tags:
                print(f"       Tags: {', '.join('#' + t for t in profile.tags)}")
            
            if profile.is_hologram:
                color = profile.calibration.neon_color
                print(f"       Color: RGB{color} | Glow: {profile.calibration.glow_intensity:.1f}")
            
            print()
        
        print("="*80 + "\n")
    
    def search_profiles(self, query: str) -> List[CalibrationProfile]:
        """Search profiles by name, description, or tags"""
        query_lower = query.lower()
        results = []
        
        for profile in self.profiles.values():
            if (query_lower in profile.name.lower() or
                query_lower in profile.description.lower() or
                any(query_lower in tag.lower() for tag in profile.tags)):
                results.append(profile)
        
        return sorted(results, key=lambda p: (-int(p.is_favorite), -p.use_count))
    
    def clear_all_profiles(self, confirm: bool = False) -> bool:
        """Delete all profiles (dangerous!)"""
        if not confirm:
            print("⚠️ WARNING: This will delete ALL profiles!")
            print("Call with confirm=True to proceed")
            return False
        
        count = len(self.profiles)
        
        for file_path in self.profiles_dir.glob("*.json"):
            if not file_path.name.startswith("_"):
                file_path.unlink()
        
        self.profiles.clear()
        self.active_profile = None
        self._save_active()
        
        print(f"🗑️ Deleted all {count} profiles")
        return True


# ═══════════════════════════════════════════════════════════════════════════
# ⬡ QUICK HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def create_hologram_profile(manager: ProfileManager, name: str, 
                           calibration_data: CalibrationData = None,
                           theme: str = "cyan") -> Optional[CalibrationProfile]:
    """Quick create hologram profile"""
    return manager.create_hologram_profile(name, calibration_data, theme)


def quick_setup_hologram(manager: ProfileManager) -> CalibrationProfile:
    """Quick setup default hologram profile"""
    cal_data = CalibrationData(
        hologram_mode=True,
        neon_color=(0, 255, 255),
        glow_intensity=1.5,
        scan_line_speed=1.0,
        particle_density=75,
        grid_enabled=True
    )
    
    profile = manager.create_profile(
        name="Default Hologram",
        calibration_data=cal_data,
        description="Default cyberpunk hologram configuration",
        icon="⬡",
        hologram_mode=True,
        tags=["hologram", "default", "cyberpunk"]
    )
    
    manager.set_active("Default Hologram")
    return profile


def setup_preset_profiles(manager: ProfileManager):
    """Setup common preset profiles"""
    presets = [
        ("Sitting Standard", "🪑", "Standard sitting at desk", False, ["posture"]),
        ("Standing", "🧍", "Standing position", False, ["posture"]),
        ("Hologram Cyan", "⬡", "Cyan hologram theme", True, ["hologram", "cyan"]),
        ("Hologram Purple", "⬡", "Purple hologram theme", True, ["hologram", "purple"]),
        ("Left Hand", "🤚", "Left hand optimized", False, ["hand", "left"]),
        ("Right Hand", "✋", "Right hand optimized", False, ["hand", "right"]),
    ]
    
    created = 0
    for name, icon, desc, is_hologram, tags in presets:
        if name not in manager.profiles:
            cal_data = CalibrationData(hologram_mode=is_hologram)
            if is_hologram:
                if "purple" in tags:
                    cal_data.neon_color = (255, 0, 255)
                else:
                    cal_data.neon_color = (0, 255, 255)
            
            manager.create_profile(name, cal_data, desc, icon, is_hologram, tags)
            created += 1
    
    print(f"✅ Setup complete: {created} preset profiles created")


# ═══════════════════════════════════════════════════════════════════════════
# ⬡ DEMO / TESTING
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║  ⬡ CALIBRATION PROFILES MODULE V3.0 — HOLOGRAM EDITION ⬡                   ║
║  Testing Profile Management System                                           ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Create manager
    manager = ProfileManager()
    
    # Setup presets
    setup_preset_profiles(manager)
    
    # Create some test hologram profiles
    manager.create_hologram_profile("Matrix Mode", theme="green")
    manager.create_hologram_profile("Neon Dreams", theme="purple")
    
    # List all profiles
    manager.list_profiles()
    
    # Show statistics
    manager.print_stats()
    
    # Test active profile
    manager.set_active("Matrix Mode")
    active = manager.get_active()
    if active:
        print(f"\n✅ Active Profile: {active.display_name}")
        print(f"   Hologram: {active.is_hologram}")
        print(f"   Color: RGB{active.calibration.neon_color}")
    
    print("\n✨ Profile system ready!")