"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                              AUREVIX LAUNCHER                                ║
║                    Visual Studio Entry Point Redirect                        ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import sys
import runpy
from pathlib import Path

if __name__ == "__main__":
    # Ensure current directory is at the beginning of sys.path
    app_dir = Path(__file__).resolve().parent
    if str(app_dir) not in sys.path:
        sys.path.insert(0, str(app_dir))

    # Delegate execution to main.py
    main_script = app_dir / "main.py"
    runpy.run_path(str(main_script), run_name="__main__")
