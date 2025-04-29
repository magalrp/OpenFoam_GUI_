"""
Módulo de configuración global del proyecto.
Aquí puedes definir constantes, rutas por defecto, valores por defecto, 
o funciones para cargar/escribir configuraciones.
"""

import os

# Ruta base del proyecto (puedes ajustarla según tus necesidades)
BASE_DIR = r"D:\1_Personal\8_OPENFOAM\OpenFoam_GUI"

# Caso de prueba por defecto (puedes cambiarlo posteriormente desde la interfaz)
DEFAULT_CASE_DIR = os.path.join(BASE_DIR, "00_Test_Case")

# Unidades por defecto para distintas magnitudes (ejemplo)
DEFAULT_TEMPERATURE_UNIT = "K"
DEFAULT_VELOCITY_UNIT = "m/s"
DEFAULT_FLOW_RATE_UNIT = "kg/s"

# Lista de especies por defecto (se utiliza si no se pasan otras)
DEFAULT_SPECIES = ["CH4", "O2", "N2", "CO2", "H2O"]

# Valores predeterminados para el solver y configuraciones relacionadas
DEFAULT_SIMULATION_TYPE = "Estacionario"
DEFAULT_CALCULATION_TYPE = "Incompresible"
DEFAULT_SOLVER = "icoFoam"

# Rutas predeterminadas para bibliotecas de materiales y especies
MATERIALS_LIBRARY_PATH = os.path.join(BASE_DIR, "core", "materials_library.py")
SPECIES_LIBRARY_PATH = os.path.join(BASE_DIR, "core", "species_library.py")

# Función para obtener la ruta del archivo boundary dado el caso
def get_boundary_file_path(case_dir=DEFAULT_CASE_DIR):
    return os.path.join(case_dir, "constant", "polyMesh", "boundary")

# Función para cargar la biblioteca de materiales
def load_materials_library():
    """Carga la biblioteca de materiales desde el archivo correspondiente."""
    from core.materials_library import MATERIALS_LIBRARY
    return MATERIALS_LIBRARY

# Función para cargar la biblioteca de especies
def load_species_library():
    """Carga la biblioteca de especies como texto."""
    from core.species_library import get_species_library
    return get_species_library()

# Aquí puedes agregar más funciones o clases relacionadas con la configuración global
# por ejemplo, carga de plantillas, escritura de archivos de configuración, etc.
