# Biblioteca general de materiales
MATERIALS_LIBRARY = {
    "air": {"density": 1.225, "viscosity": 1.81e-5, "specific_heat": 1005, "thermal_conductivity": 0.0257},
    "water_liquid": {"density": 997, "viscosity": 0.001, "specific_heat": 4184, "thermal_conductivity": 0.6},
    "water_vapor": {"density": 0.804, "viscosity": 1.34e-5, "specific_heat": 2010, "thermal_conductivity": 0.0259},
    "helium": {"density": 0.1786, "viscosity": 1.96e-5, "specific_heat": 5193, "thermal_conductivity": 0.1513},
    "argon": {"density": 1.784, "viscosity": 2.12e-5, "specific_heat": 520.3, "thermal_conductivity": 0.0163},
    "hydrogen": {"density": 0.0899, "viscosity": 8.41e-6, "specific_heat": 14300, "thermal_conductivity": 0.1805},
    "methane": {"density": 0.656, "viscosity": 1.08e-5, "specific_heat": 2180, "thermal_conductivity": 0.034},
    "propane": {"density": 2.01, "viscosity": 8.37e-6, "specific_heat": 1670, "thermal_conductivity": 0.0165},
    "ethanol": {"density": 789, "viscosity": 0.0012, "specific_heat": 2440, "thermal_conductivity": 0.171},
    "glycerol": {"density": 1260, "viscosity": 1.412, "specific_heat": 2410, "thermal_conductivity": 0.285},
    "aluminum": {"density": 2700, "specific_heat": 900, "thermal_conductivity": 237},
    "copper": {"density": 8960, "specific_heat": 385, "thermal_conductivity": 401},
    "iron": {"density": 7874, "specific_heat": 449, "thermal_conductivity": 80.2},
    "steel": {"density": 7850, "specific_heat": 500, "thermal_conductivity": 50},
    "glass": {"density": 2500, "specific_heat": 840, "thermal_conductivity": 1.05},
    "rubber": {"density": 1522, "specific_heat": 1800, "thermal_conductivity": 0.2},
    "concrete": {"density": 2300, "specific_heat": 880, "thermal_conductivity": 1.4},
    "silicon": {"density": 2329, "specific_heat": 700, "thermal_conductivity": 149},
    "oil": {"density": 870, "viscosity": 0.1, "specific_heat": 2000, "thermal_conductivity": 0.15},
    "nitrogen": {"density": 1.2506, "viscosity": 1.76e-5, "specific_heat": 1040, "thermal_conductivity": 0.0242}
}

def get_material_properties(material_name):
    """Devuelve las propiedades del material especificado."""
    return MATERIALS_LIBRARY.get(material_name, None)

def list_all_materials():
    """Devuelve una lista de todos los materiales disponibles en la biblioteca."""
    return list(MATERIALS_LIBRARY.keys())
