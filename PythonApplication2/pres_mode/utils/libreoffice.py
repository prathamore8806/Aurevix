"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                         📎 LIBREOFFICE UTILITIES                             ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import shutil
import subprocess
import tempfile
from typing import Optional

from .cleanup import register_temp_directory, cleanup_single_directory


# ═══════════════════════════════════════════════════════════════════════════════
#                         🔍 LIBREOFFICE DETECTION
# ═══════════════════════════════════════════════════════════════════════════════

def find_libreoffice() -> Optional[str]:
    """
    Find LibreOffice installation path.
    
    Returns:
        Path to soffice executable, or None if not found
    """
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
            
    else:  # Linux and others
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


def is_libreoffice_available() -> bool:
    """
    Check if LibreOffice is available.
    
    Returns:
        True if LibreOffice is found, False otherwise
    """
    return find_libreoffice() is not None


# ═══════════════════════════════════════════════════════════════════════════════
#                         📄 PDF CONVERSION
# ═══════════════════════════════════════════════════════════════════════════════

def convert_to_pdf(
    input_file: str,
    output_dir: Optional[str] = None,
    timeout: int = 180
) -> Optional[str]:
    """
    Convert a file to PDF using LibreOffice.
    
    Args:
        input_file: Path to input file (PPT, PPTX, DOC, etc.)
        output_dir: Directory for output PDF (default: temp directory)
        timeout: Conversion timeout in seconds (default: 180)
    
    Returns:
        Path to converted PDF, or None if conversion failed
    
    Raises:
        FileNotFoundError: If LibreOffice is not installed
        FileNotFoundError: If input file doesn't exist
        RuntimeError: If conversion fails
    """
    # Find LibreOffice
    libreoffice_path = find_libreoffice()
    if not libreoffice_path:
        raise FileNotFoundError(
            "LibreOffice not found. Install from: https://www.libreoffice.org/download/"
        )
    
    # Validate input file
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    # Create output directory if needed
    cleanup_temp = False
    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="libreoffice_convert_")
        register_temp_directory(output_dir)
        cleanup_temp = True
    elif not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Build command
        cmd = [
            libreoffice_path,
            '--headless',
            '--invisible',
            '--convert-to', 'pdf',
            '--outdir', output_dir,
            input_file
        ]
        
        # Windows-specific: hide console window
        startupinfo = None
        if sys.platform == 'win32':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
        
        # Run conversion
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            startupinfo=startupinfo
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"LibreOffice conversion failed: {result.stderr}")
        
        # Find the output PDF
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        pdf_path = os.path.join(output_dir, f"{base_name}.pdf")
        
        if not os.path.exists(pdf_path):
            # Try to find any PDF in output directory
            pdf_files = [f for f in os.listdir(output_dir) if f.endswith('.pdf')]
            if pdf_files:
                pdf_path = os.path.join(output_dir, pdf_files[0])
            else:
                raise RuntimeError("No PDF file was generated")
        
        return pdf_path
        
    except subprocess.TimeoutExpired:
        if cleanup_temp:
            cleanup_single_directory(output_dir)
        raise RuntimeError(f"Conversion timed out after {timeout} seconds")
        
    except Exception as e:
        if cleanup_temp:
            cleanup_single_directory(output_dir)
        raise


def convert_ppt_to_images(
    input_file: str,
    output_dir: Optional[str] = None,
    dpi: int = 150,
    timeout: int = 180
) -> list:
    """
    Convert PPT/PPTX to images via PDF intermediate.
    
    Args:
        input_file: Path to PPT/PPTX file
        output_dir: Directory for output images (default: temp directory)
        dpi: Image resolution (default: 150)
        timeout: Conversion timeout in seconds (default: 180)
    
    Returns:
        List of paths to generated images
    
    Raises:
        ImportError: If PyMuPDF is not available
        FileNotFoundError: If LibreOffice is not installed
        RuntimeError: If conversion fails
    """
    # Import here to avoid circular dependency
    from ..config.dependencies import PDF_AVAILABLE, fitz
    
    if not PDF_AVAILABLE:
        raise ImportError("PyMuPDF is required for image conversion. Run: pip install PyMuPDF")
    
    # Convert to PDF first
    pdf_path = convert_to_pdf(input_file, timeout=timeout)
    
    if not pdf_path:
        raise RuntimeError("Failed to convert to PDF")
    
    # Create output directory for images
    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="ppt_images_")
        register_temp_directory(output_dir)
    elif not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    image_paths = []
    
    try:
        # Open PDF and convert each page to image
        doc = fitz.open(pdf_path)
        
        scale = dpi / 72.0
        mat = fitz.Matrix(scale, scale)
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            pix = page.get_pixmap(matrix=mat)
            
            image_path = os.path.join(output_dir, f"slide_{page_num + 1:03d}.png")
            pix.save(image_path)
            image_paths.append(image_path)
        
        doc.close()
        
        return image_paths
        
    except Exception as e:
        raise RuntimeError(f"Failed to convert PDF to images: {e}")