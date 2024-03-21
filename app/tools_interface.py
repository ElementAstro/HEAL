import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QListWidget, QComboBox, QDialog, QDialogButtonBox, QLineEdit
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
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search...")
        self.search_input.textChanged.connect(self.filter_telescopes)
        self.layout.addWidget(self.search_input)

        # Sort by combobox
        self.sort_combobox = QComboBox()
        self.sort_combobox.addItems(["Make", "Model", "Aperture", "Focal Length"])
        self.sort_combobox.currentIndexChanged.connect(self.sort_telescopes)
        self.layout.addWidget(self.sort_combobox)

        # Telescopes list
        self.telescopes_list = QListWidget()
        self.populate_telescopes()
        self.layout.addWidget(self.telescopes_list)

        self.setLayout(self.layout)

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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TelescopeCatalog()
    window.show()
    sys.exit(app.exec())
