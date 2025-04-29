# ui/conf/constant/conf_particleTrack.py
import os

def generate_particleTrackProperties(case_config, output_file):
    """
    Genera el archivo particleTrackProperties para OpenFOAM basándose en la configuración
    almacenada en case_config["particleTrackProperties"].

    La estructura del archivo es la siguiente:

    /*--------------------------------*- C++ -*----------------------------------*\
    | =========                 |                                                 |
    | \      /  Field         | OpenFOAM: The Open Source CFD Toolbox           |
    |  \    /   Operation     | Version:  v2406                                 |
    |   \  /    And           | Website:  www.openfoam.com                      |
    |    \/     Manipulation  |                                                 |
    \*---------------------------------------------------------------------------*/
    FoamFile
    {
        version     2.0;
        format      ascii;
        class       dictionary;
        object      particleTrackProperties;
    }
    // * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

    cloud           <cloudName>;

    sampleFrequency <sampleFrequency>;

    maxPositions    <maxPositions>;

    [parámetros extra]

    // ************************************************************************* //
    """
    # Extraer la configuración de particle tracking
    track_config = case_config.get("particleTrackProperties", {})
    cloud = track_config.get("cloudName", "reactingCloud1")
    sampleFrequency = track_config.get("sampleFrequency", 1)
    maxPositions = track_config.get("maxPositions", 1000000)
    
    extra_lines = []
    if "setFormat" in track_config and track_config["setFormat"]:
        extra_lines.append(f"setFormat       {track_config['setFormat']};")
    if "fields" in track_config and track_config["fields"]:
        extra_lines.append(f"fields          {track_config['fields']};")
    if "maxTracks" in track_config:
        extra_lines.append(f"maxTracks       {track_config['maxTracks']};")
    
    header = """/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\      /  Field         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\    /   Operation     | Version:  v2406                                 |
|   \\  /    And           | Website:  www.openfoam.com                      |
|    \\/     Manipulation  |                                                 |
\\*---------------------------------------------------------------------------*/
FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      particleTrackProperties;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //
"""
    body = f"""
cloud           {cloud};

sampleFrequency {sampleFrequency};

maxPositions    {int(maxPositions)};
"""
    if extra_lines:
        body += "\n" + "\n".join(extra_lines) + "\n"
    footer = "\n// ************************************************************************* //\n"
    
    content = header + body + footer
    with open(output_file, "w") as f:
        f.write(content)

if __name__ == "__main__":
    # Ejemplo de uso:
    import os
    example_config = {
        "particleTrackProperties": {
            "cloudName": "genericCloud",
            "sampleFrequency": 1,
            "maxPositions": 2000000.0,
            "setFormat": "vtk",
            "fields": "",
            "maxTracks": -1
        }
    }
    output_file = os.path.abspath("particleTrackProperties")
    generate_particleTrackProperties(example_config, output_file)
