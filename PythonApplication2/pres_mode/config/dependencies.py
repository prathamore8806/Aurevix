"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                         📦 DEPENDENCY CHECKS                                 ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import shutil

# ═══════════════════════════════════════════════════════════════════════════════
#                         📦 PyMuPDF (PDF Support)
# ═══════════════════════════════════════════════════════════════════════════════

fitz = None
PDF_AVAILABLE = False

try:
    import fitz  # PyMuPDF
    PDF_AVAILABLE = True
    print("✅ PyMuPDF available - PDF support enabled")
except ImportError:
    PDF_AVAILABLE = False
    print("⚠️ PyMuPDF not installed. Run: pip install PyMuPDF")


# ═══════════════════════════════════════════════════════════════════════════════
#                         📦 python-pptx (PPTX Support)
# ═══════════════════════════════════════════════════════════════════════════════

PPTXPresentation = None
Inches = None
Pt = None
Emu = None
MSO_SHAPE_TYPE = None
PP_ALIGN = None
PPTX_AVAILABLE = False

try:
    from pptx import Presentation as PPTXPresentation
    from pptx.util import Inches, Pt, Emu
    from pptx.enum.shapes import MSO_SHAPE_TYPE
    try:
        from pptx.enum.text import PP_ALIGN
    except:
        PP_ALIGN = None
    PPTX_AVAILABLE = True
    print("✅ python-pptx available - PPTX support enabled")
except ImportError:
    PPTX_AVAILABLE = False
    PP_ALIGN = None
    print("⚠️ python-pptx not installed. Run: pip install python-pptx")


# ═══════════════════════════════════════════════════════════════════════════════
#                         📦 comtypes (Windows PowerPoint COM)
# ═══════════════════════════════════════════════════════════════════════════════

comtypes = None
pythoncom = None
COMTYPES_AVAILABLE = False

try:
    import comtypes.client
    import pythoncom
    comtypes = comtypes
    COMTYPES_AVAILABLE = True
    print("✅ comtypes available - PowerPoint COM support enabled")
except ImportError:
    COMTYPES_AVAILABLE = False
    print("⚠️ comtypes not installed (Windows PowerPoint automation)")


# ═══════════════════════════════════════════════════════════════════════════════
#                         🔍 LIBREOFFICE DETECTION
# ═══════════════════════════════════════════════════════════════════════════════

def _find_libreoffice():
    """Find LibreOffice installation path"""
    possible_paths = []
    
    if sys.platform == 'win32':
        possible_paths = [
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
            r"C:\Program Files\LibreOffice\program\soffice.com",
            os.path.expandvars(r"%PROGRAMFILES%\LibreOffice\program\soffice.exe"),
            os.path.expandvars(r"%PROGRAMFILES(X86)%\LibreOffice\program\soffice.exe"),
        ]
        which_result = shutil.which("soffice")
        if which_result:
            possible_paths.insert(0, which_result)
            
    elif sys.platform == 'darwin':
        possible_paths = [
            "/Applications/LibreOffice.app/Contents/MacOS/soffice",
            os.path.expanduser("~/Applications/LibreOffice.app/Contents/MacOS/soffice"),
        ]
        which_result = shutil.which("soffice")
        if which_result:
            possible_paths.insert(0, which_result)
            
    else:
        possible_paths = [
            "/usr/bin/soffice",
            "/usr/bin/libreoffice",
            "/usr/local/bin/soffice",
            "/usr/local/bin/libreoffice",
            "/snap/bin/libreoffice",
            os.path.expanduser("~/.local/bin/soffice"),
        ]
        which_result = shutil.which("soffice") or shutil.which("libreoffice")
        if which_result:
            possible_paths.insert(0, which_result)
    
    for path in possible_paths:
        if path and os.path.exists(path):
            return path
    return None


LIBREOFFICE_PATH = _find_libreoffice()
LIBREOFFICE_AVAILABLE = LIBREOFFICE_PATH is not None

if LIBREOFFICE_AVAILABLE:
    print(f"✅ LibreOffice found: {LIBREOFFICE_PATH}")
else:
    print("⚠️ LibreOffice not found. Install from: https://www.libreoffice.org/download/")


# ═══════════════════════════════════════════════════════════════════════════════
#                         📋 DEPENDENCY SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════

def print_dependency_status():
    """Print status of all dependencies"""
    print("\n" + "=" * 50)
    print("📦 DEPENDENCY STATUS")
    print("=" * 50)
    print(f"  {'✅' if PDF_AVAILABLE else '❌'} PDF Support (PyMuPDF)")
    print(f"  {'✅' if PPTX_AVAILABLE else '❌'} PPTX Support (python-pptx)")
    print(f"  {'✅' if COMTYPES_AVAILABLE else '❌'} COM Support (comtypes)")
    print(f"  {'✅' if LIBREOFFICE_AVAILABLE else '❌'} LibreOffice")
    print("=" * 50 + "\n")


def get_ppt_support_available():
    """Check if any PPT conversion method is available"""
    return LIBREOFFICE_AVAILABLE or COMTYPES_AVAILABLE or PPTX_AVAILABLE