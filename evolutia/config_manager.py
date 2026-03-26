#!/usr/bin/env python3
"""
Gestor de configuración automática.
Genera config.yaml basado en la estructura del proyecto y metadatos de archivos.
"""
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Set, Any, Union, Optional
import json
try:
    import jsonschema
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Directorios a excluir de la búsqueda de temas
EXCLUDED_DIRS = {
    'evolutia', 
    #'examenes', 
    #'tareas', 
    'proyecto', 
    '_build', 
    '.git', 
    '__pycache__',
    '.ipynb_checkpoints',
    'images',
    'static',
    'storage',
    'thumbnails',
    'config'
}

class ConfigManager:
    def __init__(self, base_path: Union[Path, str], config_path: Optional[Union[Path, str]] = None):
        self.base_path = Path(base_path)

        if config_path:
            self.config_path = Path(config_path)
        else:
            # Intentar encontrar evolutia_config.yaml en la raíz
            root_config = self.base_path / 'evolutia_config.yaml'
            if root_config.exists():
                self.config_path = root_config
            else:
               # Default interno: ubicado en el paquete instalado
               # Obtenemos la ruta de este archivo (config_manager.py) -> parent (evolutia/) -> config -> config.yaml
               self.config_path = Path(__file__).parent / 'config' / 'config.yaml'
        
        if self.config_path.exists():
            logger.info(f"Usando archivo de configuración: {self.config_path}")
        else:
            logger.info(f"Archivo de configuración no encontrado en {self.config_path}. Usando configuración por defecto.")

    def validate_config(self, config_data: Dict[str, Any]) -> bool:
        """Valida la configuración contra el esquema JSON."""
        if not JSONSCHEMA_AVAILABLE:
            logger.warning("jsonschema no instalado, omitiendo validación de esquema.")
            return True

        # Buscar schema
        # Intentar rutas relativas comunes
        schema_path = Path(__file__).parent / 'schemas' / 'config.schema.json'
        
        if not schema_path.exists():
             logger.warning(f"No se encontró esquema en {schema_path}, omitiendo validación.")
             return True

        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema = json.load(f)
            
            jsonschema.validate(instance=config_data, schema=schema)
            logger.info("Configuración válida según esquema.")
            return True
        except jsonschema.exceptions.ValidationError as e:
            logger.error(f"Error de validación de configuración: {e.message}")
            logger.error(f"Ruta del error: {' -> '.join([str(p) for p in e.path])}")
            return False
        except Exception as e:
            logger.error(f"Error inesperado validando esquema: {e}")
            return False
        
    def load_current_config(self) -> Dict[str, Any]:
        """Carga la configuración actual si existe."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f) or {}

                    # Validar esquema JSON si está disponible
                    if config and not self.validate_config(config):
                        logger.warning("Configuración inválida según esquema JSON, pero continuando...")

                    # Validar valores con ConfigValidator
                    from .validation import ConfigValidator
                    validator = ConfigValidator()
                    is_valid, errors = validator.validate_config(config)

                    if not is_valid:
                        logger.error("Errores de validación en configuración:")
                        for error in errors:
                            logger.error(f"  - {error}")
                        logger.warning("Continuando con configuración inválida (puede causar errores)")

                    return config
            except Exception as e:
                logger.error(f"Error leyendo config actual: {e}")
                return {}
        return {}

    def discover_topics(self) -> List[str]:
        """Descubre directorios de temas basados en la existencia de archivos .md."""
        topics = []
        for p in self.base_path.iterdir():
            if p.is_dir() and p.name not in EXCLUDED_DIRS and not p.name.startswith('.'):
                # Verificar si contiene archivos markdown relevantes (lecturas o prácticas)
                md_files = list(p.glob("*.md"))
                if md_files:
                    topics.append(p.name)
        return sorted(topics)

    def extract_keywords_from_topic(self, topic: str) -> List[str]:
        """Extrae keywords de los archivos del tema."""
        topic_dir = self.base_path / topic
        keywords_set: Set[str] = set()
        
        # Buscar en todos los md, pero priorizar lecturas
        for md_file in topic_dir.glob("*.md"):
            try:
                content = md_file.read_text(encoding='utf-8')
                # Extracción simple de frontmatter yaml
                if content.startswith('---'):
                    end_fm = content.find('---', 3)
                    if end_fm != -1:
                        fm_text = content[3:end_fm]
                        fm = yaml.safe_load(fm_text)
                        if fm and 'keywords' in fm:
                            kw = fm['keywords']
                            if isinstance(kw, list):
                                keywords_set.update(kw)
                            elif isinstance(kw, str):
                                keywords_set.add(kw)
            except Exception as e:
                logger.warning(f"No se pudo leer keywords de {md_file}: {e}")
                
        return sorted(list(keywords_set))

    def update_config(self):
        """Actualiza el archivo de configuración."""
        current_config = self.load_current_config()
        
        # Descubrir temas
        topics = self.discover_topics()
        logger.info(f"Temas encontrados: {topics}")
        
        # Extraer keywords por tema
        topic_keywords = {}
        for topic in topics:
            kws = self.extract_keywords_from_topic(topic)
            if kws:
                topic_keywords[topic] = kws
                logger.info(f"Keywords para {topic}: {len(kws)}")
            else:
                logger.warning(f"No se encontraron keywords para {topic}")

        # Estructura base si no existe
        if 'paths' not in current_config:
            current_config['paths'] = {'base_path': '..'}
        
        if 'exam' not in current_config:
            current_config['exam'] = {
                'default': {
                    'subject': "IF3602 - II semestre 2025",
                    'points_per_exercise': 25,
                    'duration_hours': 2.0
                }
            }
            
        # Actualizar valores dinámicos
        current_config['paths']['materials_directories'] = topics
        
        if 'keywords' not in current_config['exam']:
            current_config['exam']['keywords'] = {}
            
        # Mezclar keywords existentes con nuevas (priorizando las extraídas si se prefiere, o haciendo merge)
        # Aquí reemplazamos para reflejar el estado actual del proyecto
        current_config['exam']['keywords'] = topic_keywords

        # Guardar configuración
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(current_config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
            
        logger.info(f"Configuración actualizada en {self.config_path}")

    def update_config_from_structure(self):
        """Alias para update_config, usado por compatibilidad."""
        return self.update_config()

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Gestor de configuración automática de Evolutia')
    parser.add_argument('--config', type=str, help='Ruta al archivo de configuración a actualizar')
    parser.add_argument('--base_path', type=str, default='.', help='Ruta base del proyecto')
    args = parser.parse_args()

    base_path = Path(args.base_path).resolve()
    # Si estamos ejecutando desde evolutia (y no se dio base_path explícito), subir un nivel
    if args.base_path == '.' and base_path.name == 'evolutia':
        base_path = base_path.parent
        
    config_path = Path(args.config) if args.config else None
        
    manager = ConfigManager(base_path, config_path)
    manager.update_config()

if __name__ == '__main__':
    main()
