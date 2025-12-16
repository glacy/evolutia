"""
Generador de archivos de examen en formato MyST/Markdown.
Crea la estructura completa de archivos para un examen.
"""
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ExamGenerator:
    """Genera archivos de examen en formato MyST/Markdown."""
    
    def __init__(self, base_path: Path):
        """
        Inicializa el generador.
        
        Args:
            base_path: Ruta base del proyecto
        """
        self.base_path = Path(base_path)
    
    def generate_exam_frontmatter(self, exam_number: int, subject: str = "IF3602 - II semestre 2025",
                                  tags: List[str] = None) -> str:
        """
        Genera el frontmatter YAML para un examen.
        
        Args:
            exam_number: Número del examen
            subject: Asignatura
            tags: Lista de tags agregados
        """
        if tags is None:
            tags = []
        
        frontmatter = {
            'title': f'Examen  {exam_number}',
            'description': f'Examen  {exam_number}',
            'short_title': f'Examen  {exam_number}',
            'author': ' ',
            'tags': tags,
            'subject': subject,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'downloads': []
        }
        
        # Convertir a YAML
        yaml_str = yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True, sort_keys=False)
        return f"---\n{yaml_str}---\n\n"
    
    def generate_instructions_block(self) -> str:
        """
        Genera el bloque de instrucciones del examen.
        
        Returns:
            String con el bloque de instrucciones en formato MyST
        """
        instructions = """:::{hint} Instrucciones
:class: dropdown

- Dispone de 2,0 horas para realizar el  examen, **individualmente**.
- Debe mostrar la cédula de identidad o carnet universitario cuando se le solicite.
- La prueba tiene un valor de 100 puntos.
- Resuelva de forma razonada cada uno de los ejercicios.
- Use esquemas y dibujos si lo considera necesario.
- Debe incluir los cálculos y procedimientos que le llevan a su respuesta.
- Debe resolver el examen en un cuaderno de examen u hojas debidamente engrapadas, utilizando lapicero de tinta de color azul o negra.
- Si utiliza lápiz, corrector, lapicero de tinta roja o borrable, no se aceptarán reclamos.
- Sólo se evaluará lo escrito en el cuaderno de examen.
- Puede hacer uso únicamente de los materiales del curso; por medio de una computadora del aula C1-04. **No se permite el uso del teclado ni de herramientas de Inteligencia Artificial**.
- Una vez que el examen haya comenzado, quienes lleguen dentro de los primeros 30 minutos podrán realizarlo, pero solo dispondrán del tiempo restante.
- No se permitirá la salida del aula a ninguna persona estudiante durante los primeros 30 minutos de aplicación, salvo casos de fuerza mayor.
- Debe apagar y guardar su celular, tableta, reloj o cualquier otro dispositivo inteligente durante el desarrollo de la prueba.

:::
"""
        return instructions
    
    def generate_exercise_section(self, exercise_num: int, exam_num: int, 
                                  points: int = 25) -> str:
        """
        Genera la sección de un ejercicio en el examen principal.
        
        Args:
            exercise_num: Número del ejercicio
            exam_num: Número del examen
            points: Puntos del ejercicio
        
        Returns:
            String con la sección del ejercicio
        """
        exercise_label = f"ex{exercise_num}_e{exam_num}"
        solution_label = f"solucion-ex{exercise_num}_e{exam_num}"
        exercise_file = f"./ex{exercise_num}_e{exam_num}.md"
        solution_file = f"./solucion_ex{exercise_num}_e{exam_num}.md"
        
        section = f"""## Ejercicio {exercise_num} [{points} puntos]
````{{exercise}} {exercise_num}
:label: {exercise_label}

```{{include}} {exercise_file}

```

````

````{{solution}} {exercise_label}
:label: {solution_label}
:class: dropdown


```{{include}} {solution_file}

```
````

"""
        return section
    
    def generate_exercise_file(self, exercise_content: str, exercise_num: int, 
                               exam_num: int, metadata: Dict = None) -> str:
        """
        Genera el contenido de un archivo de ejercicio individual.
        
        Args:
            exercise_content: Contenido del ejercicio
            exercise_num: Número del ejercicio
            exam_num: Número del examen
            metadata: Metadatos opcionales (generator, model, date)
        
        Returns:
            Contenido del archivo
        """
        content = ""
        if metadata:
            frontmatter = {
                'generator': 'evolutia',
                'source': 'ai_variation',
                'date': datetime.now().isoformat()
            }
            frontmatter.update(metadata)
            yaml_str = yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True, sort_keys=False)
            content += f"---\n{yaml_str}---\n\n"
            
        content += exercise_content.strip() + "\n"
        return content
    
    def generate_solution_file(self, solution_content: str, exercise_num: int,
                               exam_num: int, metadata: Dict = None) -> str:
        """
        Genera el contenido de un archivo de solución individual.
        
        Args:
            solution_content: Contenido de la solución
            exercise_num: Número del ejercicio
            exam_num: Número del examen
            metadata: Metadatos opcionales
        
        Returns:
            Contenido del archivo
        """
        content = ""
        if metadata:
            frontmatter = {
                'generator': 'evolutia',
                'source': 'ai_solution',
                'date': datetime.now().isoformat()
            }
            frontmatter.update(metadata)
            yaml_str = yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True, sort_keys=False)
            content += f"---\n{yaml_str}---\n\n"
            
        content += solution_content.strip() + "\n"
        return content
    
    def generate_exam(self, variations: List[Dict], exam_number: int,
                      output_dir: Path, subject: str = "IF3602 - II semestre 2025",
                      keywords: List[str] = None, metadata: Dict = None) -> bool:
        """
        Genera un examen completo con todas sus variaciones.
        
        Args:
            variations: Lista de variaciones generadas (cada una debe tener
                       'variation_content' y opcionalmente 'variation_solution')
            exam_number: Número del examen
            output_dir: Directorio donde crear los archivos
            subject: Asignatura
            keywords: Palabras clave
            metadata: Metadatos generales para incluir en ejercicios (ej: model)
        
        Returns:
            True si se generó exitosamente, False en caso contrario
        """
        try:
            # Crear directorio si no existe
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Recolectar todos los tags de las variaciones
            all_tags = set()
            if keywords:
                all_tags.update(keywords)
            
            for variation in variations:
                original_frontmatter = variation.get('original_frontmatter', {})
                if 'tags' in original_frontmatter and original_frontmatter['tags']:
                    all_tags.update(original_frontmatter['tags'])
            
            # Generar archivo principal del examen
            exam_content = self.generate_exam_frontmatter(exam_number, subject, list(all_tags))
            exam_content += self.generate_instructions_block()
            exam_content += "\n"
            
            # Agregar secciones de ejercicios
            points_per_exercise = 100 // len(variations)
            for i, variation in enumerate(variations, 1):
                exam_content += self.generate_exercise_section(
                    i, exam_number, points_per_exercise
                )
            
            # Escribir archivo principal
            exam_file = output_dir / f"examen{exam_number}.md"
            with open(exam_file, 'w', encoding='utf-8') as f:
                f.write(exam_content)
            
            logger.info(f"Archivo principal creado: {exam_file}")
            
            # Generar archivos individuales de ejercicios y soluciones
            for i, variation in enumerate(variations, 1):
                # Preparar metadatos específicos de esta variación
                current_metadata = metadata.copy() if metadata else {}
                original_frontmatter = variation.get('original_frontmatter', {})
                
                # Agregar tags y subject originales si existen
                if 'tags' in original_frontmatter:
                    current_metadata['tags'] = original_frontmatter['tags']
                if 'subject' in original_frontmatter:
                    current_metadata['original_subject'] = original_frontmatter['subject']
                if 'complexity' in original_frontmatter:
                    current_metadata['complexity'] = original_frontmatter['complexity']
                
                # Add original label for traceability
                if 'original_label' in variation and variation['original_label']:
                     current_metadata['based_on'] = variation['original_label']
                
                # Add RAG references if available
                if 'rag_references' in variation and variation['rag_references']:
                    current_metadata['rag_references'] = variation['rag_references']

                # Archivo de ejercicio
                exercise_content = variation.get('variation_content', '')
                if exercise_content:
                    exercise_file = output_dir / f"ex{i}_e{exam_number}.md"
                    with open(exercise_file, 'w', encoding='utf-8') as f:
                        f.write(self.generate_exercise_file(
                            exercise_content, i, exam_number, current_metadata
                        ))
                    logger.info(f"Ejercicio creado: {exercise_file}")
                
                # Archivo de solución
                solution_content = variation.get('variation_solution', '')
                if solution_content:
                    solution_file = output_dir / f"solucion_ex{i}_e{exam_number}.md"
                    with open(solution_file, 'w', encoding='utf-8') as f:
                        f.write(self.generate_solution_file(
                            solution_content, i, exam_number, current_metadata
                        ))
                    logger.info(f"Solución creada: {solution_file}")
                else:
                    logger.warning(f"No hay solución para ejercicio {i}")
            
            # Actualizar downloads en frontmatter
            self._update_downloads_in_frontmatter(exam_file, exam_number, len(variations))
            
            return True
        except Exception as e:
            logger.error(f"Error generando examen: {e}")
            return False
    
    def _update_downloads_in_frontmatter(self, exam_file: Path, exam_number: int,
                                        num_exercises: int):
        """
        Actualiza la sección de downloads en el frontmatter del examen.
        
        Args:
            exam_file: Archivo del examen
            exam_number: Número del examen
            num_exercises: Número de ejercicios
        """
        try:
            content = exam_file.read_text(encoding='utf-8')
            
            # Extraer frontmatter
            import re
            frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
            if not frontmatter_match:
                return
            
            frontmatter_str = frontmatter_match.group(1)
            frontmatter = yaml.safe_load(frontmatter_str) or {}
            
            # Crear lista de downloads
            downloads = [
                {'file': f'./examen{exam_number}.md', 'title': f'examen{exam_number}.md'},
                {'file': f'./examen{exam_number}.pdf', 'title': f'examen{exam_number}.pdf'}
            ]
            
            for i in range(1, num_exercises + 1):
                downloads.append({
                    'file': f'./solucion_ex{i}_e{exam_number}.md',
                    'title': f'solucion_ex{i}_e{exam_number}.md'
                })
            
            frontmatter['downloads'] = downloads
            
            # Reemplazar frontmatter
            new_frontmatter_str = yaml.dump(
                frontmatter, default_flow_style=False, allow_unicode=True, sort_keys=False
            )
            new_content = f"---\n{new_frontmatter_str}---\n\n" + content[frontmatter_match.end():]
            
            exam_file.write_text(new_content, encoding='utf-8')
        except Exception as e:
            logger.warning(f"No se pudo actualizar downloads: {e}")

