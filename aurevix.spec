# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, collect_submodules

block_cipher = None

# Root directory of source code
BASE_DIR = os.path.abspath(SPECPATH if 'SPECPATH' in globals() else os.getcwd())
SRC_DIR = os.path.join(BASE_DIR, 'PythonApplication2')

# Collect MediaPipe data files & CV2 binaries
mediapipe_datas = collect_data_files('mediapipe')
cv2_datas = collect_data_files('cv2')

# Additional project assets
extra_assets = [
    (os.path.join(SRC_DIR, 'GCVM'), 'GCVM'),
    (os.path.join(SRC_DIR, '.env'), '.'),
    (os.path.join(SRC_DIR, 'gestures.json'), '.'),
    (os.path.join(SRC_DIR, 'aurevix.ico'), '.'),
    (os.path.join(SRC_DIR, 'sgcc_users.db'), '.'),
]

# Only include files that exist
existing_datas = [item for item in extra_assets if os.path.exists(item[0])]
added_datas = existing_datas + mediapipe_datas + cv2_datas

# Hidden imports for dynamic/runtime modules
hidden_imports = [
    'mediapipe',
    'cv2',
    'PySide6',
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'supabase',
    'postgrest',
    'gotrue',
    'realtime',
    'storage3',
    'supafunc',
    'dotenv',
    'pyautogui',
    'pynput',
    'speech_recognition',
    'pyttsx3',
    'pyttsx3.drivers',
    'pyttsx3.drivers.sapi5',
    'email_service',
    'supabase_manager',
    'auth_pages',
    'profile_widget',
    'top_navigation',
    'sidebar',
    'futuristic_dashboard',
    'database',
    'config',
    'hand_tracker',
    'active_ai_engine',
    'voice_command_processor',
    'audio_manager',
    'notification_manager',
    'calibration_page',
    'calibration_profiles',
    'gaming_gesture_controller',
    'logs_page',
    'settings_panel',
    'preferences_page',
    'ai_trainer_game',
    'hand_tracking',
    'hand_tracking.core',
    'hand_tracking.core.camera',
    'hand_tracking.core.filters',
    'hand_tracking.core.hud',
    'hand_tracking.core.state',
    'hand_tracking.modes',
    'hand_tracking.modes.base_mode',
    'hand_tracking.modes.desktop_mode',
    'hand_tracking.modes.gaming_mode',
    'hand_tracking.modes.draw_mode',
    'hand_tracking.modes.presentation_mode',
    'hand_tracking.ds_pipeline',
    'gaming_mode',
    'training_modes'
] + collect_submodules('mediapipe')

a = Analysis(
    [os.path.join(SRC_DIR, 'main.py')],
    pathex=[
        SRC_DIR,
        os.path.join(SRC_DIR, 'hand_tracking'),
        os.path.join(SRC_DIR, 'gaming_mode'),
        os.path.join(SRC_DIR, 'training_modes')
    ],
    binaries=collect_dynamic_libs('cv2'),
    datas=added_datas,
    hiddenimports=hidden_imports + ['matplotlib', 'matplotlib.pyplot'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'torch', 'torchvision', 'torchaudio', 'caffe2',
        'scipy', 'pandas', 'sklearn',
        'tkinter', 'IPython', 'notebook', 'pytest'
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Aurevix',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(SRC_DIR, 'aurevix.ico') if os.path.exists(os.path.join(SRC_DIR, 'aurevix.ico')) else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Aurevix',
)
