# core/json_manager.py
import json
import os

class JSONManager:
    def __init__(self, data_dir=os.path.join(os.path.dirname(__file__), '..', 'temp')):
        # Asegura que la ruta es absoluta y válida
        self.data_dir = os.path.abspath(data_dir)
        os.makedirs(self.data_dir, exist_ok=True)
        print(f"JSONManager inicializado con data_dir: {self.data_dir}")  # Línea de depuración
    
    def get_file_path(self, section_name):
        return os.path.join(self.data_dir, f"{section_name}.json")
    
    def save_section(self, section_name, data):
        file_path = self.get_file_path(section_name)
        try:
            with open(file_path, 'w') as json_file:
                json.dump(data, json_file, indent=4)
            print(f"Sección '{section_name}' guardada exitosamente en {file_path}.")  # Línea de depuración
            return True, "Guardado exitoso."
        except Exception as e:
            print(f"Error al guardar sección '{section_name}': {str(e)}")  # Línea de depuración
            return False, f"Error al guardar: {str(e)}"
    
    def load_section(self, section_name):
        file_path = self.get_file_path(section_name)
        if not os.path.exists(file_path):
            print(f"Archivo '{file_path}' no existe. Devolviendo diccionario vacío.")  # Línea de depuración
            return {}
        try:
            with open(file_path, 'r') as json_file:
                data = json.load(json_file)
            print(f"Sección '{section_name}' cargada exitosamente desde {file_path}.")  # Línea de depuración
            return data
        except Exception as e:
            print(f"Error al cargar sección '{section_name}': {str(e)}")  # Línea de depuración
            return {}
    
    def export_all(self, export_path):
        all_data = {}
        try:
            for filename in os.listdir(self.data_dir):
                if filename.endswith('.json'):
                    section = filename.replace('.json', '')
                    with open(os.path.join(self.data_dir, filename), 'r') as f:
                        all_data[section] = json.load(f)
            with open(export_path, 'w') as f:
                json.dump(all_data, f, indent=4)
            print(f"Todas las secciones exportadas exitosamente a {export_path}.")  # Línea de depuración
            return True, "Exportación exitosa."
        except Exception as e:
            print(f"Error en exportación: {str(e)}")  # Línea de depuración
            return False, f"Error en exportación: {str(e)}"
