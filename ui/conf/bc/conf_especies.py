# ui/conf/bc/conf_especies.py

import os
import logging
from core.species_library import get_species_library

def parse_species_library(species_library_str):
    """
    Parsea la cadena de la biblioteca de especies para extraer los nombres de las especies.

    Args:
        species_library_str (str): Cadena de múltiples líneas con definiciones de especies.
    Returns:
        list: Lista de nombres de especies (str).
    """
    species = []
    for line in species_library_str.splitlines():
        line = line.strip()
        if not line or line.startswith("THERMO") or line.startswith("END"):
            continue
        # Se asume que la especie es la primera palabra en la línea
        species_name = line.split()[0]
        species.append(species_name)
    return species


def generate_species_files(boundary_conditions, chosen_species, target_dir):
    """
    Genera un archivo por cada especie activa (y válida en la librería) en 'target_dir'.
    Cada archivo contiene la configuración de esa especie para todas las fronteras definidas
    en boundary_conditions.json (según su 'type': wall, inlet, outlet, etc.).
    
    Además, elimina únicamente los archivos de especie que ya no estén activos,
    sin tocar los archivos estándar de OpenFOAM (U, T, p, p_rgh, alphat, nut, k, omega, epsilon).

    Args:
        boundary_conditions (dict): Diccionario "boundaryConditions" proveniente de boundary_conditions.json.
        chosen_species (list): Lista de especies activas definidas en el modelo/química.
        target_dir (str): Directorio donde se guardarán/actualizarán los archivos de especies.
    """
    logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')

    # Asegurar la existencia del directorio de destino
    os.makedirs(target_dir, exist_ok=True)

    # Obtener la biblioteca de especies y filtrar las activas que estén en la biblioteca
    species_library_str = get_species_library()
    species_library = parse_species_library(species_library_str)
    valid_species = [s for s in chosen_species if s in species_library]

    # Advertir si hay especies no válidas
    invalid_species = set(chosen_species) - set(valid_species)
    if invalid_species:
        logging.warning(
            f"Las siguientes especies no están en la biblioteca y no serán procesadas: "
            f"{', '.join(invalid_species)}"
        )

    # Para cada especie válida, se genera un archivo con las fronteras definidas
    for species in valid_species:
        # Construir el texto del boundaryField iterando sobre cada frontera
        boundary_entries_text = ""

        for bc_name, bc_data in boundary_conditions.items():
            btype = bc_data.get("type", "").lower()
            # Por defecto: zeroGradient
            species_boundary_type = "zeroGradient"
            species_value_here = bc_data.get(f"{species}_chemValue", 0.0)  # Valor por defecto si no se encuentra

            # Decidir el "type" y la "value"
            if btype == "wall":
                # walls => zeroGradient sin "value"
                boundary_entries_text += f"""
    {bc_name}
    {{
        type            zeroGradient;
    }}
"""
            elif btype == "inlet":
                boundary_entries_text += f"""
    {bc_name}
    {{
        type            fixedValue;
        value           uniform {species_value_here};
    }}
"""
            elif btype == "outlet":
                # Se usará inletOutlet con valor = species_value_here
                boundary_entries_text += f"""
    {bc_name}
    {{
        type            inletOutlet;
        inletValue      uniform {species_value_here};
        value           uniform {species_value_here};
    }}
"""
            else:
                # Cualquier otro => zeroGradient
                boundary_entries_text += f"""
    {bc_name}
    {{
        type            zeroGradient;
    }}
"""

        # Construir el contenido final del archivo de la especie
        species_file_path = os.path.join(target_dir, species)
        species_content = f"""/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\    /   O peration     | Version:  v2406                                 |
|   \\  /    A nd           | Website:  www.openfoam.com                      |
|    \\/     M anipulation  |                                                 |
\\*---------------------------------------------------------------------------*/
FoamFile
{{
    version     2.0;
    format      ascii;
    class       volScalarField;
    object      {species};
}}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

dimensions      [0 0 0 0 0 0 0];

internalField   uniform 0.0;

boundaryField
{{{boundary_entries_text}
}}

// ************************************************************************* //
"""
        # Escribir el archivo de especie
        try:
            with open(species_file_path, "w", encoding='utf-8') as f:
                f.write(species_content)
            logging.info(f"Archivo de especie '{species}' generado/actualizado en {species_file_path}.")
        except Exception as e:
            logging.error(f"Error al generar el archivo de especie '{species}': {e}")
            raise e

    # Proteger archivos estándar y de turbulencia de OpenFOAM para no eliminarlos
    standard_non_species_files = {
        "U", "T", "p", "p_rgh", "alphat", "nut", "k", "omega", "epsilon"
    }

    # Identificar los archivos del directorio
    existing_files = set(os.listdir(target_dir))
    active_species_files = set(valid_species)

    # Los archivos de especie a eliminar son los que:
    # - Están en el directorio
    # - NO están en las especies activas
    # - NO son archivos estándar/turbulencia
    species_files_to_delete = existing_files - active_species_files - standard_non_species_files

    for species_file in species_files_to_delete:
        species_file_path = os.path.join(target_dir, species_file)
        if os.path.isfile(species_file_path):
            try:
                os.remove(species_file_path)
                logging.info(f"Archivo de especie inactiva '{species_file}' eliminado de {species_file_path}.")
            except Exception as e:
                logging.error(f"Error al eliminar '{species_file}': {e}")
