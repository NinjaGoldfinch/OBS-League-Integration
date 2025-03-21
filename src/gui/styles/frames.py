"""
Frame and label style configurations.
"""

from tkinter import ttk
from .colors import ColorScheme

def configure_frame_styles(style: ttk.Style, colors: ColorScheme):
    """Configure frame and label styles."""
    
    # Main label frame style
    style.configure(
        "Main.TLabelframe",
        background=colors.background,
        foreground=colors.foreground,
        bordercolor=colors.border,
        relief="groove",
        borderwidth=1
    )
    
    style.configure(
        "Main.TLabelframe.Label",
        background=colors.background,
        foreground=colors.accent_light,
        font=("Arial", 10, "bold")
    )
    
    # Title label style
    style.configure(
        "Title.TLabel",
        background=colors.background,
        foreground=colors.secondary_fg,
        font=("Arial", 9)
    )
    
    # Frame style
    style.configure(
        "TFrame",
        background=colors.background
    )

def configure_status_styles(style: ttk.Style, colors: ColorScheme):
    """Configure status display styles."""
    
    style.configure(
        "Status.TLabel",
        background=colors.background,
        foreground=colors.accent_light,
        font=("Arial", 9, "bold"),
        padding=(5, 2)
    )
    
    style.map(
        "Status.TLabel",
        foreground=[
            ("disabled", colors.disabled_fg),
            ("readonly", colors.secondary_fg)
        ]
    )