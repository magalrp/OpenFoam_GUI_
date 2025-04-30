import json
import os
import logging
from jsonschema import validate, ValidationError

class JSONManager:
    def __init__(self, data_dir=None):
        # Por defecto, carpeta temp junto al módulo
        if data_dir is None:
            base = os.path.dirname(__file__)
            data_dir = os.path.abspath(os.path.join(base, '..', 'temp'))
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        logging.debug(f"JSONManager inicializado con data_dir: {self.data_dir}")

        # Carpeta de esquemas
        base = os.path.dirname(__file__)
        self.schema_dir = os.path.abspath(os.path.join(base, '..', 'schema'))

    def get_file_path(self, section_name):
        return os.path.join(self.data_dir, f"{section_name}.json")

    def get_schema_path(self, section_name):
        return os.path.join(self.schema_dir, f"{section_name}.schema.json")

    def load_schema(self, section_name):
        schema_path = self.get_schema_path(section_name)
        if os.path.exists(schema_path):
            with open(schema_path, 'r') as f:
                return json.load(f)
        return None

    def save_section(self, section_name, data):
        """Valida y guarda una sección en JSON."""
        # Validar contra esquema si existe
        schema = self.load_schema(section_name)
        if schema:
            try:
                validate(instance=data, schema=schema)
                logging.debug(f"Validación exitosa de esquema para '{section_name}'.")
            except ValidationError as e:
                logging.error(f"Error de validación en sección '{section_name}': {e.message}")
                return False, f"Validación fallida: {e.message}"

        # Guardar archivo
        file_path = self.get_file_path(section_name)
        try:
            with open(file_path, 'w') as json_file:
                json.dump(data, json_file, indent=4)
            logging.info(f"Sección '{section_name}' guardada en {file_path}.")
            return True, "Guardado exitoso."
        except Exception as e:
            logging.error(f"Error al guardar sección '{section_name}': {e}")
            return False, f"Error al guardar: {str(e)}"

    def load_section(self, section_name):
        """Carga JSON y opcionalmente lo valida."""
        file_path = self.get_file_path(section_name)
        if not os.path.exists(file_path):
            logging.debug(f"No existe {file_path}. Devolviendo dict vacío.")
            return {}

        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            logging.info(f"Sección '{section_name}' cargada desde {file_path}.")
        except Exception as e:
            logging.error(f"Error al cargar sección '{section_name}': {e}")
            return {}

        # Validar datos cargados
        schema = self.load_schema(section_name)
        if schema:
            try:
                validate(instance=data, schema=schema)
                logging.debug(f"Validación exitosa tras carga para '{section_name}'.")
            except ValidationError as e:
                logging.error(f"Datos inválidos en '{section_name}': {e.message}")
                # opcionalmente, podrías devolver {} o alertar al usuario
        return data

    def export_all(self, export_path):
        """Exporta todas las secciones juntas."""
        all_data = {}
        try:
            for filename in os.listdir(self.data_dir):
                if filename.endswith('.json'):
                    section = filename.replace('.json', '')
                    with open(os.path.join(self.data_dir, filename), 'r') as f:
                        all_data[section] = json.load(f)
            with open(export_path, 'w') as f:
                json.dump(all_data, f, indent=4)
            logging.info(f"Todas las secciones exportadas a {export_path}.")
            return True, "Exportación exitosa."
        except Exception as e:
            logging.error(f"Error en export_all: {e}")
            return False, f"Error en exportación: {str(e)}"
