# ui/conf/constant/conf_thermophysicalProperties.py

import os
import logging

THERMO_TEMPLATE = """/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\    /   O peration     | Version:  {version}                                 |
|   \\  /    A nd           | Website:  www.openfoam.com                      |
|    \\/     M anipulation  |                                                 |
\\*---------------------------------------------------------------------------*/
FoamFile
{{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      thermophysicalProperties;
}}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

thermoType
{{
    type            {type};
    mixture         {mixture};
    transport       {transport};
    thermo          {thermo};
    energy          {energy};
    equationOfState {equationOfState};
    specie          {specie};
}}

CHEMKINFile         "{chemkin_dir}/chem.inp";
CHEMKINThermoFile   "{chemkin_dir}/therm.dat";
CHEMKINTransportFile "{chemkin_dir}/transportProperties";

newFormat       {newFormat};

inertSpecie     {inertSpecie};

liquids
{{
{liquids}
}}

solids
{{
{solids}
}}

// ************************************************************************* //
"""

def generate_thermophysicalProperties(settings: dict, target_path: str):
    """
    Escribe el archivo thermophysicalProperties en target_path
    usando los valores de settings.
    Claves esperadas en settings:
      - version
      - type, mixture, transport, thermo, energy, equationOfState, specie
      - chemkin_dir
      - newFormat
      - inertSpecie
      - liquids (lista de strings)
      - solids  (lista de strings)
    """
    os.makedirs(os.path.dirname(target_path), exist_ok=True)

    # Formatear listas
    liquids_block = "\n".join(f"    {liq};" for liq in settings.get("liquids", []))
    solids_block  = "\n".join(f"    {sol};" for sol in settings.get("solids",  []))

    content = THERMO_TEMPLATE.format(
        version           = settings.get("version", "v2406"),
        type              = settings["type"],
        mixture           = settings["mixture"],
        transport         = settings["transport"],
        thermo            = settings["thermo"],
        energy            = settings["energy"],
        equationOfState   = settings["equationOfState"],
        specie            = settings["specie"],
        chemkin_dir       = settings.get("chemkin_dir", "<case>/chemkin"),
        newFormat         = "yes" if settings.get("newFormat", True) else "no",
        inertSpecie       = settings.get("inertSpecie", "N2"),
        liquids           = liquids_block,
        solids            = solids_block
    )

    try:
        with open(target_path, 'w') as f:
            f.write(content)
        logging.info(f"'thermophysicalProperties' escrito en: {target_path}")
    except Exception as e:
        logging.error(f"Error al escribir '{target_path}': {e}")
        raise
