def parse_openfoam_boundary(boundary_file_path):
    """
    Parsea el archivo 'boundary' de un caso de OpenFOAM y extrae 
    la información sobre las fronteras.

    Parámetros
    ----------
    boundary_file_path : str
        Ruta completa al archivo 'boundary' dentro de constant/polyMesh/

    Retorna
    -------
    list of dict
        Una lista de diccionarios, cada uno representando una frontera con las llaves:
        {
          "name": str,
          "type": str,
          "nFaces": int,
          "startFace": int
        }
    """
    boundaries = []
    with open(boundary_file_path, 'r') as f:
        lines = f.readlines()

    # Eliminamos espacios vacíos y líneas en blanco
    lines = [line.strip() for line in lines if line.strip()]

    # Buscar número de patches
    num_boundaries = None
    start_index = None
    for i, line in enumerate(lines):
        if line.isdigit():
            # Encontramos una línea con un dígito, comprobar la siguiente línea para '('
            if i+1 < len(lines) and lines[i+1] == '(':
                num_boundaries = int(line)
                start_index = i+2
                break

    if num_boundaries is None or start_index is None:
        raise ValueError("No se pudo encontrar el número de patches y el '(' en el archivo boundary.")

    i = start_index
    patches_leidos = 0
    while i < len(lines) and patches_leidos < num_boundaries:
        boundary_name = lines[i].strip()
        i += 1

        if i >= len(lines) or lines[i] != '{':
            raise ValueError(f"Se esperaba '{{' después del nombre de la frontera {boundary_name}")
        i += 1

        boundary_type = None
        nFaces = None
        startFace = None

        while i < len(lines) and lines[i] != '}':
            line = lines[i]
            if line.startswith('type'):
                boundary_type = line.replace('type', '').replace(';', '').strip()
            elif line.startswith('nFaces'):
                nFaces_str = line.replace('nFaces', '').replace(';', '').strip()
                nFaces = int(nFaces_str)
            elif line.startswith('startFace'):
                startFace_str = line.replace('startFace', '').replace(';', '').strip()
                startFace = int(startFace_str)
            i += 1

        if i >= len(lines) or lines[i] != '}':
            raise ValueError(f"No se encontró '}}' al final del bloque de la frontera {boundary_name}")
        i += 1

        boundaries.append({
            "name": boundary_name,
            "type": boundary_type,
            "nFaces": nFaces,
            "startFace": startFace
        })
        patches_leidos += 1

    return boundaries
