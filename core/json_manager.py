# core/json_manager.py

import os
import json
from jsonschema import validate, ValidationError

class JSONManager:
    def __init__(self, data_dir=None):
        # Por defecto, carpeta temp junto al módulo
        if data_dir is None:
            base = os.path.dirname(__file__)
            data_dir = os.path.abspath(os.path.join(base, '..', 'temp'))
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        print(f"[JSONManager] Inicializado con data_dir: {self.data_dir}")

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
            try:
                with open(schema_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"[JSONManager] Error leyendo esquema {schema_path}: {e}")
        return None

    def save_section(self, section_name, data):
        """
        Valida (si hay esquema) y guarda la sección en JSON.
        Devuelve (True, mensaje) o (False, mensaje_error).
        """
        # 1) validación
        schema = self.load_schema(section_name)
        if schema:
            try:
                validate(instance=data, schema=schema)
                print(f"[JSONManager] Validación exitosa para sección '{section_name}'.")
            except ValidationError as e:
                msg = f"Validación fallida en '{section_name}': {e.message}"
                print(f"[JSONManager] {msg}")
                return False, msg

        # 2) guardado
        file_path = self.get_file_path(section_name)
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w') as json_file:
                json.dump(data, json_file, indent=4)
            print(f"[JSONManager] Sección '{section_name}' guardada en {file_path}")
            return True, "Guardado exitoso."
        except Exception as e:
            msg = f"Error al guardar '{section_name}.json': {e}"
            print(f"[JSONManager] {msg}")
            return False, msg

    def load_section(self, section_name):
        """
        Carga la sección desde JSON, valida (si hay esquema) y devuelve el dict.
        """
        file_path = self.get_file_path(section_name)
        if not os.path.exists(file_path):
            print(f"[JSONManager] '{section_name}.json' no existe, devolviendo {{}}")
            return {}

        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            print(f"[JSONManager] Sección '{section_name}' cargada desde {file_path}")
        except Exception as e:
            print(f"[JSONManager] Error leyendo '{section_name}.json': {e}")
            return {}

        # validación post‐carga
        schema = self.load_schema(section_name)
        if schema:
            try:
                validate(instance=data, schema=schema)
                print(f"[JSONManager] Validación post-carga exitosa para '{section_name}'.")
            except ValidationError as e:
                print(f"[JSONManager] Datos inválidos en '{section_name}': {e.message}")
        return data

    def export_all(self, export_path):
        """
        Junta todas las secciones JSON y las vuelca en un único archivo.
        """
        all_data = {}
        try:
            for fn in os.listdir(self.data_dir):
                if fn.endswith('.json'):
                    sec = fn[:-5]
                    with open(os.path.join(self.data_dir, fn), 'r') as f:
                        all_data[sec] = json.load(f)
            with open(export_path, 'w') as f:
                json.dump(all_data, f, indent=4)
            print(f"[JSONManager] Todas las secciones exportadas a {export_path}")
            return True, "Exportación exitosa."
        except Exception as e:
            msg = f"Error en export_all: {e}"
            print(f"[JSONManager] {msg}")
            return False, msg
