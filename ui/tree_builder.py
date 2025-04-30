# ui/tree_builder.py

from PyQt5.QtWidgets import QTreeWidgetItem
from PyQt5.QtGui import QFont

# Define aquí la jerarquía y las claves que luego enlazaremos con los widgets de página
TREE_STRUCTURE = [
    {
        "label": "Caso",
        "key": "case",
        "children": [
            {"label": "Directorio de trabajo",   "key": "directorio"},
            {"label": "Modelos",                 "key": "modelos"},
            {"label": "Materiales",              "key": "materiales"},
            {"label": "Condiciones de contorno", "key": "boundary_conditions"},
            {"label": "Fase discreta",           "key": "fase_discreta"}
        ]
    },
    {
        "label": "Solucionador",
        "key": "solver",
        "children": [
            {"label": "Métodos",         "key": "methods"},
            {"label": "Controles",       "key": "controls"},
            {"label": "Inicialización",  "key": "inicializacion"},
            {"label": "Ejecutar cálculo","key": "run_calculation"}
            
        ]
    }
]

class TreeBuilder:
    @staticmethod
    def build(tree_widget):
        """
        Construye el QTreeWidget según TREE_STRUCTURE.
        Devuelve un dict: { clave: QTreeWidgetItem } para hacer el mapeo a páginas.
        """
        tree_widget.clear()
        # Fuente en negrita para los nodos raíz
        bold = QFont(tree_widget.font())
        bold.setBold(True)

        item_map = {}
        for section in TREE_STRUCTURE:
            root = QTreeWidgetItem([section["label"]])
            root.setFont(0, bold)
            tree_widget.addTopLevelItem(root)

            for child in section["children"]:
                node = QTreeWidgetItem([child["label"]])
                root.addChild(node)
                item_map[child["key"]] = node

        tree_widget.expandAll()
        return item_map