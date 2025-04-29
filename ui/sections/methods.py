# ui/sections/methods.py

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLabel,
    QComboBox, QGroupBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from core.json_manager import JSONManager

class Methods(QWidget):
    """
    Sección 'Methods' para definir los esquemas de discretización en fvSchemes.
    Incluye ddtSchemes, gradSchemes, divSchemes, laplacianSchemes,
    interpolationSchemes, snGradSchemes y wallDist.method.
    Guarda y carga la configuración en fvSchemes.json.
    """
    data_changed = pyqtSignal()

    def __init__(self, case_config):
        super().__init__()
        self.case_config = case_config
        self.json = JSONManager()

        # Opciones de esquemas según guía OpenFOAM
        self.ddt_schemes   = ["Euler", "backward", "CrankNicolson"]
        self.grad_schemes  = ["Gauss linear", "Gauss upwind", "Gauss limitedLinear"]
        self.div_schemes   = ["none", "Gauss linear", "Gauss upwind", "Gauss limitedLinear"]
        self.lapl_schemes  = ["Gauss linear uncorrected", "Gauss linear corrected"]
        self.interp_schemes = ["linear", "cubic"]
        self.sn_grad_schemes = ["uncorrected", "corrected"]
        self.wall_dist_methods = ["meshWave", "distanceToBoundary", "inverseDistance"]

        # Cargar persistencia previa
        stored = self.json.load_section("fvSchemes") or {}
        self.case_config.setdefault("fvSchemes", {})
        self.case_config["fvSchemes"].update(stored)

        # Layout
        layout = QVBoxLayout(self)
        title = QLabel("Methods")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-weight:bold; font-size:16px;")
        layout.addWidget(title)

        desc = QLabel(
            "Selecciona los esquemas numéricos para: ddt, gradientes, divergencias,"
            " laplacianos, interpolaciones, snGrad y método wallDist."
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)

        form = QFormLayout()

        # ddtSchemes
        self.ddt_combo = QComboBox()
        self.ddt_combo.addItems(self.ddt_schemes)
        self.ddt_combo.setCurrentText(
            self.case_config["fvSchemes"].get("ddtSchemes", self.ddt_schemes[0])
        )
        form.addRow("ddtSchemes:", self.ddt_combo)

        # gradSchemes
        self.grad_combo = QComboBox()
        self.grad_combo.addItems(self.grad_schemes)
        self.grad_combo.setCurrentText(
            self.case_config["fvSchemes"].get("gradSchemes", self.grad_schemes[0])
        )
        form.addRow("gradSchemes:", self.grad_combo)

        # divSchemes
        self.div_combo = QComboBox()
        self.div_combo.addItems(self.div_schemes)
        self.div_combo.setCurrentText(
            self.case_config["fvSchemes"].get("divSchemes", self.div_schemes[0])
        )
        form.addRow("divSchemes:", self.div_combo)

        # laplacianSchemes
        self.lapl_combo = QComboBox()
        self.lapl_combo.addItems(self.lapl_schemes)
        self.lapl_combo.setCurrentText(
            self.case_config["fvSchemes"].get("laplacianSchemes", self.lapl_schemes[0])
        )
        form.addRow("laplacianSchemes:", self.lapl_combo)

        # interpolationSchemes
        self.interp_combo = QComboBox()
        self.interp_combo.addItems(self.interp_schemes)
        self.interp_combo.setCurrentText(
            self.case_config["fvSchemes"].get("interpolationSchemes", self.interp_schemes[0])
        )
        form.addRow("interpolationSchemes:", self.interp_combo)

        # snGradSchemes
        self.snp_combo = QComboBox()
        self.snp_combo.addItems(self.sn_grad_schemes)
        self.snp_combo.setCurrentText(
            self.case_config["fvSchemes"].get("snGradSchemes", self.sn_grad_schemes[0])
        )
        form.addRow("snGradSchemes:", self.snp_combo)

        # wallDist.method
        self.wall_combo = QComboBox()
        self.wall_combo.addItems(self.wall_dist_methods)
        self.wall_combo.setCurrentText(
            self.case_config["fvSchemes"].get("wallDist" , self.wall_dist_methods[0])
        )
        form.addRow("wallDist.method:", self.wall_combo)

        layout.addLayout(form)
        layout.addStretch()

        # Conectar cambios
        for combo in [
            self.ddt_combo, self.grad_combo, self.div_combo,
            self.lapl_combo, self.interp_combo,
            self.snp_combo, self.wall_combo
        ]:
            combo.currentTextChanged.connect(self._on_changed)

    def _on_changed(self, _=None):
        # Recoger esquemas y persistir
        schemes = {
            "ddtSchemes": self.ddt_combo.currentText(),
            "gradSchemes": self.grad_combo.currentText(),
            "divSchemes": self.div_combo.currentText(),
            "laplacianSchemes": self.lapl_combo.currentText(),
            "interpolationSchemes": self.interp_combo.currentText(),
            "snGradSchemes": self.snp_combo.currentText(),
            "wallDist": self.wall_combo.currentText()
        }
        self.case_config["fvSchemes"].update(schemes)
        self.json.save_section("fvSchemes", schemes)
        self.data_changed.emit()
