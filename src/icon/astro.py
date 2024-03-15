from enum import Enum

from qfluentwidgets import getIconColor, Theme, FluentIconBase


class AstroIcon(FluentIconBase, Enum):
    """ Custom icons """

    ASCOM = "ASCOM"
    INDI = "INDI"
    INDIGO = "INDIGO"

    APT = "APT"
    NINA = "N.I.N.A"
    SharpCap = "SharpCap"
    FireCpature = "FireCapture"
    SGP = "SGP"
    MaximDL = "MaximDL"
    TheSky = "TheSky"
    Voyager = "Voyager"

    PHD = "PHD"

    def path(self, theme=Theme.AUTO):
        # getIconColor() 根据主题返回字符串 "white" 或者 "black"
        return f'./icons/{self.value}.svg'
