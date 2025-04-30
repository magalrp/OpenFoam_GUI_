# ui/sections/visualizer_panel.py

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt

class VisualizerPanel(QWidget):
    """
    Panel de visualización deshabilitado.
    Muestra un mensaje informativo en lugar del visualizador 3D.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        # Texto informativo centrado
        label = QLabel("Ventana de visualización:\naccesible en futuras versiones")
        label.setAlignment(Qt.AlignCenter)
        label.setWordWrap(True)
        layout.addWidget(label)
        self.setLayout(layout)
