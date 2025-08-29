import os
from enum import Enum, unique

from qfluentwidgets import FluentIconBase, Theme, getIconColor

from . import resource_manager


@unique
class AstroIconBase(FluentIconBase, Enum):
    """Base class for Astro Icons"""

    def path(self, theme: Theme = Theme.AUTO) -> str:
        return str(resource_manager.get_resource_path("app_icons", f"{self.value}.svg"))


# Function to dynamically load icons
def load_icons() -> dict[str, str]:
    icons_dir = "./icons"
    icons: dict[str, str] = {}
    if os.path.exists(icons_dir):
        for file in os.listdir(icons_dir):
            if file.endswith(".svg"):
                icon_name = file[:-4]  # Remove the .svg extension
                icons[icon_name] = file
    return icons


# Create the AstroIcon class dynamically
icons = load_icons()
# Create a simple enum that mypy can understand


class AstroIcon(AstroIconBase):
    """Dynamically created Astro Icons"""
    pass


# Add icons as class attributes if they exist
if icons:
    for name in icons.keys():
        setattr(AstroIcon, name.upper(), name)
else:
    # Fallback if no icons found
    setattr(AstroIcon, 'DEFAULT', 'default')

# Testing - example to show usage
if __name__ == "__main__":
    # Simple test without dynamic access
    print("AstroIcon class created successfully")
