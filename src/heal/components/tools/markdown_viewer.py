# markdown_viewer.py
from .markdown_renderer import MarkdownRenderer  # Import the new renderer
import os
import sys
from dataclasses import dataclass
from typing import Any, Optional

import markdown
from PySide6.QtCore import QPoint, Qt, QThread, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    CheckBox,
    FluentIcon,
    LineEdit,
    MessageBox,
    ProgressBar,
    PushButton,
    Slider,
    SubtitleLabel,
    TextEdit,
    ToolButton,
)

from src.heal.common.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class Theme:
    background: str
    color: str
    editor_background: str
    editor_color: str
    preview_background: str
    preview_color: str
    border_color: str


class TitleBar(QWidget):
    """Custom Title Bar"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(40)
        self.parent_widget = parent
        self.init_ui()

    def init_ui(self) -> None:
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 0, 10, 0)

        # Title Label
        self.title_label = SubtitleLabel("Markdown Editor")
        self.title_label.setFont(QFont("Arial", 14))
        layout.addWidget(self.title_label)

        layout.addStretch()

        # Minimize Button
        self.minimize_button = ToolButton()
        self.minimize_button.setIcon(FluentIcon.MINIMIZE)
        if self.parent_widget:
            self.minimize_button.clicked.connect(
                self.parent_widget.showMinimized)
        layout.addWidget(self.minimize_button)

        # Maximize/Restore Button
        self.maximize_button = ToolButton()
        self.maximize_button.setIcon(FluentIcon.ADD)
        self.maximize_button.clicked.connect(self.toggle_maximize)
        layout.addWidget(self.maximize_button)

        # Close Button
        self.close_button = ToolButton()
        self.close_button.setIcon(FluentIcon.DELETE)
        if self.parent_widget:
            self.close_button.clicked.connect(self.parent_widget.close)
        layout.addWidget(self.close_button)

        self.setLayout(layout)

    def toggle_maximize(self) -> None:
        if self.parent_widget:
            if self.parent_widget.isMaximized():
                self.parent_widget.showNormal()
                self.maximize_button.setIcon(FluentIcon.WINDOW_MAXIMIZE)
                logger.info("Window restored to normal size.")
            else:
                self.parent_widget.showMaximized()
                self.maximize_button.setIcon(FluentIcon.WINDOW_RESTORE)
                logger.info("Window maximized.")

    def mousePressEvent(self, event: Any) -> None:
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPosition().toPoint()
            event.accept()

    def mouseMoveEvent(self, event: Any) -> None:
        if event.buttons() == Qt.LeftButton and self.parent_widget:
            self.parent_widget.move(
                self.parent_widget.pos()
                + event.globalPosition().toPoint()
                - self.drag_position
            )
            self.drag_position = event.globalPosition().toPoint()
            event.accept()


class LoadFileThread(QThread):
    """Thread to load file to prevent UI blocking."""

    file_loaded = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, file_path: str) -> None:
        super().__init__()
        self.file_path = file_path

    def run(self) -> None:
        try:
            with open(self.file_path, "r", encoding="utf-8") as file:
                markdown_text = file.read()
            self.file_loaded.emit(markdown_text)
        except Exception as e:
            self.error_occurred.emit(str(e))


class MarkdownEditor(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        # Window Settings
        self.setWindowTitle("Markdown Editor")
        self.resize(1200, 800)
        self.setWindowFlags(Qt.FramelessWindowHint)  # Remove default title bar

        # Initialize Themes
        self.light_theme = Theme(
            background="#ffffff",
            color="#000000",
            editor_background="#ffffff",
            editor_color="#000000",
            preview_background="#f5f5f5",
            preview_color="#333333",
            border_color="#ddd",
        )
        self.dark_theme = Theme(
            background="#2b2b2b",
            color="#ffffff",
            editor_background="#3c3f41",
            editor_color="#ffffff",
            preview_background="#3c3f41",
            preview_color="#ffffff",
            border_color="#555555",
        )
        self.current_theme = self.light_theme

        logger.info("Application started.")

        # Central Widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Initialize UI
        self.init_ui()

    def init_ui(self) -> None:
        """Initialize the user interface."""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.central_widget.setLayout(main_layout)

        # Title Bar
        title_bar = TitleBar(self)
        main_layout.addWidget(title_bar)

        # Toolbar Layout
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(10, 10, 10, 10)

        # Load Button
        self.load_button = PushButton(
            text="Load Markdown", icon=FluentIcon.ADD_TO)
        self.load_button.clicked.connect(self.load_markdown_file)
        toolbar_layout.addWidget(self.load_button)

        # Save Button
        self.save_button = PushButton(
            text="Save as Markdown", icon=FluentIcon.SAVE)
        self.save_button.clicked.connect(self.save_markdown_file)
        toolbar_layout.addWidget(self.save_button)

        # Export to HTML Button
        self.export_button = PushButton(
            text="Export to HTML", icon=FluentIcon.CLOUD)
        self.export_button.clicked.connect(self.export_to_html)
        toolbar_layout.addWidget(self.export_button)

        # Export to PDF Button
        self.export_pdf_button = PushButton(
            text="Export to PDF", icon=FluentIcon.DOCUMENT  # Assume FILE_PDF exists
        )
        self.export_pdf_button.clicked.connect(self.export_to_pdf)
        toolbar_layout.addWidget(self.export_pdf_button)

        # Copy Content Button
        self.copy_button = PushButton(
            text="Copy Content", icon=FluentIcon.COPY)
        self.copy_button.clicked.connect(self.copy_content)
        toolbar_layout.addWidget(self.copy_button)

        # Dark Mode Toggle
        self.theme_switch = CheckBox("Dark Mode")
        self.theme_switch.stateChanged.connect(self.toggle_theme)
        toolbar_layout.addWidget(self.theme_switch)

        # Add Toolbar to Main Layout
        main_layout.addLayout(toolbar_layout)

        # Editor and Preview Layout
        editor_preview_layout = QHBoxLayout()
        editor_preview_layout.setContentsMargins(10, 0, 10, 10)
        editor_preview_layout.setSpacing(10)

        # Markdown Editor
        self.editor = TextEdit()
        self.editor.setPlaceholderText("Enter Markdown content here...")
        self.editor.textChanged.connect(self.update_preview)
        self.apply_theme_to_editor()
        editor_preview_layout.addWidget(self.editor)

        # Markdown Preview
        self.preview = QTextBrowser()
        self.renderer = MarkdownRenderer(self.preview)  # Use the new renderer
        self.apply_theme_to_preview()
        editor_preview_layout.addWidget(self.preview)

        # Add Editor and Preview Layout to Main Layout
        main_layout.addLayout(editor_preview_layout)

        # Bottom Toolbar Layout
        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(10, 0, 10, 10)

        # Font Size Adjustment
        self.font_label = SubtitleLabel("Font Size:")
        bottom_layout.addWidget(self.font_label)

        self.font_slider = Slider(Qt.Horizontal)
        self.font_slider.setMinimum(10)
        self.font_slider.setMaximum(24)
        self.font_slider.setValue(14)
        self.font_slider.sliderReleased.connect(self.change_font_size)
        bottom_layout.addWidget(self.font_slider)

        # Search Options
        self.search_input = LineEdit()
        self.search_input.setPlaceholderText("Search keyword...")
        self.search_input.textChanged.connect(self.highlight_search)
        bottom_layout.addWidget(self.search_input)

        self.case_checkbox = CheckBox("Case Sensitive")
        self.case_checkbox.stateChanged.connect(self.highlight_search)
        bottom_layout.addWidget(self.case_checkbox)

        self.whole_word_checkbox = CheckBox("Whole Words")
        self.whole_word_checkbox.stateChanged.connect(self.highlight_search)
        bottom_layout.addWidget(self.whole_word_checkbox)

        # Add Bottom Toolbar to Main Layout
        main_layout.addLayout(bottom_layout)

        # Loading Progress Bar
        self.progress_bar = ProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

    def apply_theme_to_editor(self) -> None:
        """Apply the current theme to the editor."""
        style = f"""
            TextEdit {{
                background-color: {self.current_theme.editor_background};
                color: {self.current_theme.editor_color};
                font-family: "Arial", sans-serif;
                border: 1px solid {self.current_theme.border_color};
                border-radius: 5px;
            }}
        """
        self.editor.setStyleSheet(style)
        logger.debug("Applied theme to editor.")

    def apply_theme_to_preview(self) -> None:
        """Apply the current theme to the preview area."""
        style = f"""
            QTextBrowser {{
                background-color: {self.current_theme.preview_background};
                color: {self.current_theme.preview_color};
                font-family: "Arial", sans-serif;
                padding: 10px;
                border: 1px solid {self.current_theme.border_color};
                border-radius: 5px;
            }}
        """
        self.preview.setStyleSheet(style)
        logger.debug("Applied theme to preview.")

    def update_preview(self) -> None:
        """Update the markdown preview."""
        markdown_text = self.editor.toPlainText()
        self.renderer.render(markdown_text)
        logger.debug("Preview updated.")

    def load_markdown_file(self) -> None:
        """Load a markdown file with loading animation."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Markdown File", "", "Markdown Files (*.md);;All Files (*)"
        )
        if file_path:
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate progress
            self.thread = LoadFileThread(file_path)
            self.thread.file_loaded.connect(self.on_file_loaded)
            self.thread.error_occurred.connect(self.on_load_error)
            self.thread.start()

    def on_file_loaded(self, markdown_text: str) -> None:
        """Handle the file loaded signal."""
        self.editor.setPlainText(markdown_text)
        self.progress_bar.setVisible(False)
        logger.info("Markdown file loaded successfully.")
        MessageBox.information(
            self, "Success", "Markdown file loaded successfully.")

    def on_load_error(self, error_message: str) -> None:
        """Handle the file load error."""
        self.progress_bar.setVisible(False)
        logger.error(f"Failed to load file: {error_message}")
        MessageBox.warning(
            self, "Error", f"Failed to load file: {error_message}")

    def save_markdown_file(self) -> None:
        """Save the current markdown content."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Markdown File", "", "Markdown Files (*.md);;All Files (*)"
        )
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as file:
                    file.write(self.editor.toPlainText())
                logger.info(f"Saved Markdown file: {file_path}")
                MessageBox.information(
                    self, "Success", "Markdown file saved successfully."
                )
            except Exception as e:
                logger.error(f"Failed to save file {file_path}: {e}")
                MessageBox.warning(self, "Error", f"Failed to save file: {e}")

    def export_to_html(self) -> None:
        """Export markdown content to HTML."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export to HTML", "", "HTML Files (*.html);;All Files (*)"
        )
        if file_path:
            try:
                html = markdown.markdown(
                    self.editor.toPlainText(), extensions=["fenced_code", "tables"]
                )
                with open(file_path, "w", encoding="utf-8") as file:
                    file.write(html)
                logger.info(f"Exported HTML file: {file_path}")
                MessageBox.information(
                    self, "Success", "Exported to HTML successfully."
                )
            except Exception as e:
                logger.error(f"Failed to export HTML {file_path}: {e}")
                MessageBox.warning(
                    self, "Error", f"Failed to export HTML: {e}")

    def export_to_pdf(self) -> None:
        """Export markdown content to PDF."""
        from PySide6.QtGui import QTextDocument
        from PySide6.QtPrintSupport import QPrinter

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export to PDF", "", "PDF Files (*.pdf);;All Files (*)"
        )
        if file_path:
            try:
                printer = QPrinter(QPrinter.HighResolution)
                printer.setOutputFormat(QPrinter.PdfFormat)
                printer.setOutputFileName(file_path)
                printer.setPageMargins(15, 15, 15, 15, QPrinter.Millimeter)

                doc = QTextDocument()
                doc.setHtml(self.preview.toHtml())
                doc.print(printer)

                logger.info(f"Exported PDF file: {file_path}")
                MessageBox.information(
                    self, "Success", "Exported to PDF successfully.")
            except Exception as e:
                logger.error(f"Failed to export PDF {file_path}: {e}")
                MessageBox.warning(self, "Error", f"Failed to export PDF: {e}")

    def copy_content(self) -> None:
        """Copy the editor content to clipboard."""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.editor.toPlainText())
        logger.info("Copied editor content to clipboard.")
        MessageBox.information(self, "Success", "Content copied to clipboard.")

    def toggle_theme(self, state: int) -> None:
        """Toggle between light and dark themes."""
        if state == Qt.Checked:
            self.current_theme = self.dark_theme
            logger.info("Switched to dark theme.")
        else:
            self.current_theme = self.light_theme
            logger.info("Switched to light theme.")
        self.apply_theme()

    def apply_theme(self) -> None:
        """Apply the current theme to all components."""
        self.setStyleSheet(
            f"background-color: {self.current_theme.background}; color: {self.current_theme.color};"
        )
        self.apply_theme_to_editor()
        self.apply_theme_to_preview()
        self.update_preview()
        logger.debug("Applied theme to all components.")

    def change_font_size(self) -> None:
        """Change the font size of the editor and preview after slider is released."""
        value = self.font_slider.value()
        font = QFont("Arial", value)
        self.editor.setFont(font)
        self.preview.setFont(font)
        logger.info(f"Changed font size to: {value}px")

    def highlight_search(self) -> None:
        """Highlight the search keyword in the preview with additional options."""
        keyword = self.search_input.text()
        case_sensitive = self.case_checkbox.isChecked()
        whole_words = self.whole_word_checkbox.isChecked()

        if not keyword:
            self.update_preview()
            return

        markdown_text = self.editor.toPlainText()

        flags = 0
        if not case_sensitive:
            flags = 0x00000001  # re.IGNORECASE equivalent

        if whole_words:
            keyword = f"\\b{keyword}\\b"

        try:
            import re

            pattern = re.compile(keyword, flags)
            highlighted_text = pattern.sub(
                lambda m: f"**{m.group(0)}**", markdown_text)
        except re.error:
            highlighted_text = markdown_text  # If regex is invalid, skip highlighting

        html = markdown.markdown(highlighted_text, extensions=[
                                 "fenced_code", "tables"])
        self.preview.setHtml(html)
        logger.info(f"Highlighted search keyword: {keyword}")


def main() -> None:
    app = QApplication(sys.argv)

    # Create main window
    window = MarkdownEditor()
    window.show()

    # Start the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
