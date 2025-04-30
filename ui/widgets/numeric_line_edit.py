from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtCore import Qt
from ui.utils.validators import get_numeric_validator

class NumericLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Aplica el validador de formato numérico
        self.setValidator(get_numeric_validator())
        # Guarda el estilo original para restaurar después
        self._default_style = self.styleSheet()
        # Conecta cambios de texto para feedback visual
        self.textChanged.connect(self._on_text_changed)

    def _on_text_changed(self, text: str):
        # Estado de validación (Acceptable, Intermediate, Invalid)
        state = self.validator().validate(text, 0)[0]
        if state != self.validator().Acceptable:
            # Borde rojo si no es aceptable
            self.setStyleSheet("border: 1px solid red;")
        else:
            # Restaura estilo original
            self.setStyleSheet(self._default_style)
