import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QDialog, QDialogButtonBox
)
from qfluentwidgets import (
    PushButton, LineEdit, ComboBox, ListWidget, FluentIcon, isDarkTheme, setTheme, Theme
)

class TelescopeCatalog(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Telescope Catalog")
        self.telescopes = [
            {"make": "Zhumell", "model": "Z12", "aperture": 304.8, "focalLength": 1500.0},
            # Add more telescope data here
        ]
        self.filtered_telescopes = self.telescopes.copy()
        
        self.layout = QVBoxLayout()

        # Search input
        self.search_input = LineEdit(self)
        self.search_input.setPlaceholderText("Search...")
        self.search_input.textChanged.connect(self.filter_telescopes)
        self.layout.addWidget(self.search_input)

        # Sort by combobox
        self.sort_combobox = ComboBox(self)
        self.sort_combobox.addItems(["Make", "Model", "Aperture", "Focal Length"])
        self.sort_combobox.currentIndexChanged.connect(self.sort_telescopes)
        self.layout.addWidget(self.sort_combobox)

        # Telescopes list
        self.telescopes_list = ListWidget(self)
        self.telescopes_list.setAlternatingRowColors(True)
        self.populate_telescopes()
        self.layout.addWidget(self.telescopes_list)

        # Add telescope button
        self.add_button = PushButton(FluentIcon.ADD, "Add Telescope", self)
        self.add_button.setIcon(FluentIcon.ADD)
        self.add_button.clicked.connect(self.add_telescope)
        self.layout.addWidget(self.add_button)

        self.setLayout(self.layout)

        # Set theme based on system settings
        setTheme(Theme.DARK if isDarkTheme() else Theme.LIGHT)

    def populate_telescopes(self):
        self.telescopes_list.clear()
        for telescope in self.filtered_telescopes:
            item = f"{telescope['make']} - {telescope['model']} - Aperture: {telescope['aperture']} mm - Focal Length: {telescope['focalLength']} mm"
            self.telescopes_list.addItem(item)

    def filter_telescopes(self):
        search_term = self.search_input.text().lower()
        self.filtered_telescopes = [telescope for telescope in self.telescopes if search_term in telescope["make"].lower() or search_term in telescope["model"].lower()]
        self.populate_telescopes()

    def sort_telescopes(self):
        sort_key = self.sort_combobox.currentText().lower().replace(" ", "")
        self.filtered_telescopes.sort(key=lambda x: x[sort_key])
        self.populate_telescopes()

    def add_telescope(self):
        dialog = AddTelescopeDialog(self)
        if dialog.exec() == QDialog.Accepted:
            telescope = dialog.get_telescope_data()
            self.telescopes.append(telescope)
            self.filtered_telescopes.append(telescope)
            self.populate_telescopes()

class AddTelescopeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Telescope")
        
        layout = QVBoxLayout()
        
        self.make_input = LineEdit(self)
        self.make_input.setPlaceholderText("Make")
        layout.addWidget(self.make_input)
        
        self.model_input = LineEdit(self)
        self.model_input.setPlaceholderText("Model")
        layout.addWidget(self.model_input)
        
        self.aperture_input = LineEdit(self)
        self.aperture_input.setPlaceholderText("Aperture (mm)")
        layout.addWidget(self.aperture_input)
        
        self.focal_length_input = LineEdit(self)
        self.focal_length_input.setPlaceholderText("Focal Length (mm)")
        layout.addWidget(self.focal_length_input)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)

    def get_telescope_data(self):
        return {
            "make": self.make_input.text(),
            "model": self.model_input.text(),
            "aperture": float(self.aperture_input.text()),
            "focalLength": float(self.focal_length_input.text())
        }


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TelescopeCatalog()
    window.show()
    sys.exit(app.exec())