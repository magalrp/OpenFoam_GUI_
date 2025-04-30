from PyQt5.QtGui import QRegularExpressionValidator
from PyQt5.QtCore import QRegularExpression

def get_numeric_validator():
    """
    Validador para números con:
      - signo opcional +/-
      - parte entera (>=1 dígito)
      - punto decimal con hasta 10 decimales
      - notación científica opcional (e±N)
    """
    regex = QRegularExpression(r"^[+-]?\d+(\.\d{1,10})?([eE][+-]?\d+)?$")
    return QRegularExpressionValidator(regex)
