# ui/sections/console_panel.py

import logging
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPlainTextEdit

class QtHandler(logging.Handler):
    """Envía los mensajes de logging a un QPlainTextEdit."""
    def __init__(self, console_widget):
        super().__init__()
        self.console = console_widget

    def emit(self, record):
        msg = self.format(record)
        # Inserta al final y desplaza
        self.console.appendPlainText(msg)

class ConsolePanel(QWidget):
    """Panel de consola con fondo blanco y texto negro."""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.log_widget = QPlainTextEdit()
        self.log_widget.setReadOnly(True)
        # Fondo blanco, texto negro
        self.log_widget.setStyleSheet("""
            QPlainTextEdit {
                background-color: white;
                color: black;
                border: 1px solid #ccc;
                font-family: monospace;
            }
        """)
        layout.addWidget(self.log_widget)
