# ui/conf/constant/conf_radiation.py
"""
Módulo para generar el archivo radiationProperties para OpenFOAM
según la configuración de radiación definida en constant.json o case_config.

El archivo se escribe de acuerdo a:
  - Si la radiación está desactivada: radiation off, radiationModel none, solverFreq 10.
  - Si está activada, se utiliza el modelo seleccionado y se incluyen parámetros adicionales
    para viewFactor, fvDOM o P1 según corresponda.
"""

def generate_radiationProperties(case_config, output_file):
    radiation_active = case_config.get("radiation_active", False)
    # Valor por defecto para solverFreq si no se especifica
    solverFreq = 10

    if not radiation_active:
        rad_status = "off"
        rad_model = "none"
        extra_params = ""
    else:
        rad_options = case_config.get("radiation_options", {})
        rad_status = "on"
        rad_model = rad_options.get("radiationModel", "viewFactor")
        solverFreq = rad_options.get("solverFreq", 10)
        extra_params = ""
        if rad_model == "viewFactor":
            nTheta = rad_options.get("nTheta", 8)
            nPhi = rad_options.get("nPhi", 8)
            extra_params = f"\n// viewFactor parameters:\n// nTheta: {nTheta}\n// nPhi: {nPhi}\n"
        elif rad_model == "fvDOM":
            nTheta = rad_options.get("nTheta", 8)
            nPhi = rad_options.get("nPhi", 8)
            phiRefValue = rad_options.get("phiRefValue", 0.0)
            extra_params = f"\n// fvDOM parameters:\n// nTheta: {nTheta}\n// nPhi: {nPhi}\n// phiRefValue: {phiRefValue}\n"
        elif rad_model == "P1":
            absorptionCoefficient = rad_options.get("absorptionCoefficient", 0.0)
            extra_params = f"\n// P1 parameters:\n// Absorption Coefficient: {absorptionCoefficient}\n"
    
    header = """/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\      /  Field         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\    /   Operation     |                                                 |
|   \\  /    And           |                                                 |
|    \\/     Manipulation  |                                                 |
\\*---------------------------------------------------------------------------*/
FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      radiationProperties;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //
"""
    content = f"""{header}
radiation       { "on" if radiation_active else "off" };

radiationModel  {rad_model};

solverFreq      {solverFreq};{extra_params}

// ************************************************************************* //
"""
    with open(output_file, "w") as f:
        f.write(content)
