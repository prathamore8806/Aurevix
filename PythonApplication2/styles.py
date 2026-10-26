import config


def get_dark_styles():
    return """
    QWidget { color: #c8d8e8; font-family: 'Inter', 'Segoe UI', sans-serif; font-size: 13pt; }
    #sidebar { background: rgba(6,6,20,0.75); border-radius: 16px;
        border: 1px solid rgba(0,212,255,0.08); }
    #sideBtn { padding: 8px 12px; border-radius: 10px; text-align: left; font-size: 12px;
        font-weight: 500; color: #5a6a7a; border: none; background: transparent; }
    #sideBtn:hover { background: rgba(0,212,255,0.08); color: #a0c0e0; }
    #sideBtn[active="true"] { background: rgba(0,212,255,0.12); color: #00d4ff;
        font-weight: 700; border-left: 3px solid #00d4ff; }
    #title { font-size: 24px; font-weight: 700; color: #e0e8f0; }
    #card { background: rgba(255,255,255,0.04); border-radius: 16px; padding: 16px;
        border: 1px solid rgba(0,212,255,0.08); }
    #card:hover { background: rgba(255,255,255,0.07); border: 1px solid rgba(0,212,255,0.15); }
    #cardTitle { font-size: 15px; font-weight: 600; color: #d0daea; }
    #modeBtn { padding: 12px; border-radius: 12px; background: rgba(255,255,255,0.05);
        border: 1px solid rgba(0,212,255,0.12); font-weight: 500; color: #a0b0c0; }
    #modeBtn:hover { background: rgba(0,212,255,0.1); color: #d0e0f0; }
    #modeBtn:checked { background: rgba(0,212,255,0.2); border: 1px solid rgba(0,212,255,0.5);
        font-weight: 700; color: #00d4ff; }
    QSlider::groove:horizontal { background: rgba(255,255,255,0.06); height: 6px; border-radius: 3px; }
    QSlider::handle:horizontal { background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 #00d4ff, stop:1 #0088cc); width: 16px; height: 16px; margin: -5px 0;
        border-radius: 8px; border: 2px solid #00a8cc; }
    QSlider::sub-page:horizontal { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #0066aa, stop:1 #00d4ff); border-radius: 3px; }
    QScrollBar:vertical { background: transparent; width: 6px; }
    QScrollBar::handle:vertical { background: rgba(0,212,255,0.2); border-radius: 3px; min-height: 30px; }
    QScrollBar::handle:vertical:hover { background: rgba(0,212,255,0.35); }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
    QStatusBar { background: transparent; color: #00d4ff; font-size: 11px; }
    QMessageBox { background: #0a0a1a; }
    QMessageBox QLabel { color: #e0e8f0; }
    """


def get_light_styles():
    return """
    QWidget { color: #1e293b; font-family: 'Inter', 'Segoe UI', sans-serif; font-size: 13pt; }
    #sidebar { background: rgba(240,245,255,0.92); border-radius: 16px; border: 1px solid rgba(0,0,0,0.06); }
    #sideBtn { padding: 8px 12px; border-radius: 10px; text-align: left; font-size: 12px;
        font-weight: 500; color: #64748b; border: none; background: transparent; }
    #sideBtn:hover { background: rgba(37,99,235,0.08); color: #1e293b; }
    #sideBtn[active="true"] { background: rgba(37,99,235,0.12); color: #2563eb; font-weight: 700;
        border-left: 3px solid #2563eb; }
    #title { font-size: 24px; font-weight: 700; color: #1e293b; }
    #card { background: rgba(255,255,255,0.92); border-radius: 16px; padding: 16px;
        border: 1px solid rgba(0,0,0,0.06); }
    #card:hover { background: rgba(255,255,255,0.96); border: 1px solid rgba(0,0,0,0.1); }
    #cardTitle { font-size: 15px; font-weight: 600; color: #1e293b; }
    #modeBtn { padding: 12px; border-radius: 12px; background: rgba(0,0,0,0.04);
        border: 1px solid rgba(0,0,0,0.08); font-weight: 500; color: #1e293b; }
    #modeBtn:hover { background: rgba(0,0,0,0.08); }
    #modeBtn:checked { background: rgba(37,99,235,0.15); border: 1px solid rgba(37,99,235,0.5);
        font-weight: 700; color: #2563eb; }
    QSlider::groove:horizontal { background: rgba(0,0,0,0.08); height: 6px; border-radius: 3px; }
    QSlider::handle:horizontal { background: #2563eb; width: 16px; height: 16px; margin: -5px 0;
        border-radius: 8px; border: 2px solid #3b82f6; }
    QSlider::sub-page:horizontal { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #1d4ed8, stop:1 #2563eb); border-radius: 3px; }
    QScrollBar:vertical { background: transparent; width: 6px; }
    QScrollBar::handle:vertical { background: rgba(0,0,0,0.15); border-radius: 3px; min-height: 30px; }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
    QStatusBar { background: transparent; color: #2563eb; font-size: 11px; }
    """


def get_styles():
    theme = getattr(config, 'theme', 'dark')
    if theme == "light":
        return get_light_styles()
    return get_dark_styles()
