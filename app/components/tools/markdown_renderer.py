# markdown_renderer.py
import markdown
from PySide6.QtWidgets import QTextBrowser
from loguru import logger

class MarkdownRenderer:
    """Markdown Rendering Component"""

    def __init__(self, preview_widget: QTextBrowser):
        self.preview = preview_widget
        logger.debug("MarkdownRenderer initialized.")

    def render(self, markdown_text: str):
        """Render Markdown to HTML and display in preview widget."""
        logger.debug("Rendering markdown text.")
        html = markdown.markdown(markdown_text, extensions=['fenced_code', 'tables'])
        self.preview.setHtml(html)
        logger.info("Markdown rendered successfully.")