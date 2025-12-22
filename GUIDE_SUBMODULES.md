# Guía: Usar Evolutia en Nuevos Cursos (Submódulos Git)

Esta guía explica cómo reutilizar el código de `evolutia` en múltiples cursos de manera limpia usando Git Submodules y la nueva funcionalidad de configuración externa.

## 1. Preparar el Repositorio Central

Primero, asegúrate de que tu versión actual de `evolutia` esté en su propio repositorio remoto (GitHub/GitLab).

1.  Ve a la carpeta de evolutia:
    ```bash
    cd ruta/a/tu/curso/actual/evolutia
    ```
2.  Asegúrate de que está limpio y actualizado:
    ```bash
    git add .
    git commit -m "Versión estable para reutilizar"
    ```
3.  Crea un nuevo repositorio en GitHub llamado `evolutia`.
4.  Enlázalo y sube el código (si no lo está ya):
    ```bash
    git remote add origin https://github.com/TU_USUARIO/evolutia.git
    git push -u origin main
    ```

## 2. Configurar el Nuevo Curso

Ahora, en tu carpeta del **Nuevo Curso**:

1.  Inicializa git (si no lo has hecho):
    ```bash
    git init
    ```
2.  Agrega `evolutia` como submódulo:
    ```bash
    git submodule add https://github.com/TU_USUARIO/evolutia.git evolutia
    ```
    *Esto descargará el código en una carpeta `evolutia/` y vinculará una versión específica.*

3.  Copia la plantilla de configuración:
    ```bash
    cp evolutia/config/config.yaml ./evolutia_config.yaml
    ```

## 3. Personalizar el Curso

Edita el archivo `evolutia_config.yaml` que acabas de crear en la raíz:

1.  **Cambia el nombre del curso**:
    ```yaml
    exam:
      default:
        subject: "Nuevo Curso 2026"
    ```
2.  **Define tus carpetas de temas**:
    (Opcional: corre `python evolutia/config_manager.py` para detectarlas automáticamente cuando tengas contenido).

## 4. Ejecutar Comandos

Ahora ejecutas el script desde la raíz del nuevo curso. Gracias a la refactorización, detectará tu config automáticamente:

```bash
# Generar examen
python evolutia/evolutia.py --tema mi_tema_nuevo --output examenes/parcial1
```

O si prefieres ser explícito:
```bash
python evolutia/evolutia.py --config ./evolutia_config.yaml --tema mi_tema_nuevo ...
```

## 5. Actualizar Evolutia

Si en el futuro mejoras `evolutia` (arreglas un bug en el curso original), solo tienes que actualizar el submódulo en el nuevo curso:

```bash
# En el nuevo curso
git submodule update --remote evolutia
```

¡Listo! Tienes una sola versión del código alimentando múltiples cursos con configuraciones independientes.
