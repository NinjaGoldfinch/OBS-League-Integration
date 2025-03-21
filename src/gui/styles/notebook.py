"""
Notebook styling configuration.
"""

from tkinter import ttk
from .theme import ColorScheme

def configure_notebook_styles(style: ttk.Style, colors: ColorScheme):
    """Configure notebook and tab styles."""
    
    # Configure notebook background
    style.configure(
        "TNotebook",
        background=colors.background,
        borderwidth=0
    )
    
    # Configure tab style
    style.configure(
        "TNotebook.Tab",
        background=colors.secondary_bg,
        foreground=colors.foreground,
        padding=(10, 2),
        font=("Arial", 9),
        borderwidth=1,
        relief="flat"
    )
    
    # Configure tab states
    style.map(
        "TNotebook.Tab",
        background=[
            ("selected", colors.background),
            ("active", colors.tertiary_bg)
        ],
        foreground=[
            ("selected", colors.accent_light),
            ("active", colors.foreground)
        ],
        expand=[
            ("selected", [1, 1, 1, 0])  # Expand selected tab slightly
        ]
    )
    
    # Remove focus dotted border
    style.layout(
        "TNotebook.Tab",
        [
            ("Notebook.tab", {
                "sticky": "nswe",
                "children": [
                    ("Notebook.padding", {
                        "side": "top",
                        "sticky": "nswe",
                        "children": [
                            ("Notebook.label", {"sticky": ""})
                        ]
                    })
                ]
            })
        ]
    )