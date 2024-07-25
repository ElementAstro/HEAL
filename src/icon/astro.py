import os
from enum import Enum, unique
from qfluentwidgets import getIconColor, Theme, FluentIconBase

@unique
class AstroIconBase(FluentIconBase, Enum):
    """ Base class for Astro Icons """
    def path(self, theme=Theme.AUTO):
        return f'./icons/{self.value}.svg'

# Function to dynamically load icons
def load_icons():
    icons_dir = './icons'
    icons = {}
    for file in os.listdir(icons_dir):
        if file.endswith('.svg'):
            icon_name = file[:-4]  # Remove the .svg extension
            icons[icon_name] = file
    return icons

# Create the AstroIcon class dynamically
icons = load_icons()
AstroIcon = Enum('AstroIcon', {name: name for name in icons.keys()}, type=AstroIconBase)

# Testing - example to show usage
if __name__ == "__main__":
    for icon in AstroIcon:
        print(icon.name, icon.path())
