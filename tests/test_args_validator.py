"""
Tests para ArgsValidator.
"""
import pytest
import argparse
from evolutia.validation.args_validator import ArgsValidator


class TestArgsValidator:
    """Test suite para ArgsValidator."""

    @pytest.fixture
    def validator(self):
        return ArgsValidator()

    @pytest.fixture
    def temp_dir(self, tmp_path):
        return tmp_path

    def test_valid_basic_args(self, validator):
        """Test args básicos válidos."""
        args = argparse.Namespace(
            tema=['analisis_vectorial'],
            num_ejercicios=3,
            output='examenes/examen1',
            complejidad='alta',
            api='openai',
            base_path='.',
            mode='variation',
            type='development',
            workers=5
        )

        is_valid, errors = validator.validate_args(args)

        assert is_valid
        assert len(errors) == 0

    def test_invalid_complejidad(self, validator):
        """Test complejidad inválida."""
        args = argparse.Namespace(
            complejidad='invalido'
        )

        is_valid, errors = validator.validate_args(args)

        assert not is_valid
        assert any('complejidad' in error.lower() for error in errors)

    def test_invalid_num_ejercicios_negative(self, validator):
        """Test num_ejercicios negativo."""
        args = argparse.Namespace(
            num_ejercicios=-1
        )

        is_valid, errors = validator.validate_args(args)

        assert not is_valid
        assert any('num_ejercicios' in error.lower() for error in errors)

    def test_num_ejercicios_too_high_warning(self, validator):
        """Test num_ejercicios muy alto (warning)."""
        args = argparse.Namespace(
            num_ejercicios=100
        )

        is_valid, errors = validator.validate_args(args)

        # Debe ser válido pero con warning
        assert is_valid
        assert len(validator.warnings) > 0
        assert any('num_ejercicios' in warning for warning in validator.warnings)

    def test_invalid_api_provider(self, validator):
        """Test proveedor de API inválido."""
        args = argparse.Namespace(
            api='invalido'
        )

        is_valid, errors = validator.validate_args(args)

        assert not is_valid
        assert any('api' in error.lower() for error in errors)

    def test_workers_too_low(self, validator):
        """Test workers muy bajo."""
        args = argparse.Namespace(
            workers=0
        )

        is_valid, errors = validator.validate_args(args)

        assert not is_valid
        assert any('workers' in error.lower() for error in errors)

    def test_workers_too_high_warning(self, validator):
        """Test workers muy alto (warning)."""
        args = argparse.Namespace(
            workers=25
        )

        is_valid, errors = validator.validate_args(args)

        assert is_valid
        assert len(validator.warnings) > 0
        assert any('workers' in warning for warning in validator.warnings)

    def test_invalid_mode(self, validator):
        """Test modo inválido."""
        args = argparse.Namespace(
            mode='invalido'
        )

        is_valid, errors = validator.validate_args(args)

        assert not is_valid
        assert any('mode' in error.lower() for error in errors)

    def test_invalid_exercise_type(self, validator):
        """Test tipo de ejercicio inválido."""
        args = argparse.Namespace(
            type='invalido'
        )

        is_valid, errors = validator.validate_args(args)

        assert not is_valid
        assert any('type' in error.lower() for error in errors)

    def test_nonexistent_base_path(self, validator):
        """Test ruta base inexistente."""
        args = argparse.Namespace(
            base_path='/ruta/que/no/existe'
        )

        is_valid, errors = validator.validate_args(args)

        assert not is_valid
        assert any('base_path' in error.lower() for error in errors)

    def test_base_path_is_file_not_dir(self, validator, temp_dir):
        """Test ruta base es archivo no directorio."""
        # Crear un archivo
        test_file = temp_dir / "test_file.txt"
        test_file.write_text("test")

        args = argparse.Namespace(
            base_path=str(test_file)
        )

        is_valid, errors = validator.validate_args(args)

        assert not is_valid
        assert any('base_path' in error.lower() for error in errors)

    def test_nonexistent_config_path(self, validator):
        """Test ruta de configuración inexistente."""
        args = argparse.Namespace(
            config='/ruta/config.yaml'
        )

        is_valid, errors = validator.validate_args(args)

        assert not is_valid
        assert any('config' in error.lower() for error in errors)

    def test_output_path_permissions(self, temp_dir):
        """Test permisos de escritura en output."""
        validator = ArgsValidator()

        # Crear directorio temporal
        temp_output = temp_dir / "output"

        args = argparse.Namespace(
            output=str(temp_output / "examen.md")
        )

        is_valid, errors = validator.validate_args(args)

        # Debe ser válido (directorio existe y es escribible)
        assert is_valid
        assert len(errors) == 0

    def test_valid_all_providers(self, validator):
        """Test todos los proveedores válidos."""
        valid_providers = ['openai', 'anthropic', 'local', 'gemini', 'deepseek', 'generic']

        for provider in valid_providers:
            args = argparse.Namespace(api=provider, base_path='.')
            is_valid, errors = validator.validate_args(args)

            assert is_valid, f"Provider {provider} debería ser válido"

    def test_valid_all_complexity_levels(self, validator):
        """Test todos los niveles de complejidad válidos."""
        valid_levels = ['media', 'alta', 'muy_alta']

        for level in valid_levels:
            args = argparse.Namespace(complejidad=level)
            is_valid, errors = validator.validate_args(args)

            assert is_valid, f"Nivel {level} debería ser válido"

    def test_valid_all_modes(self, validator):
        """Test todos los modos válidos."""
        valid_modes = ['variation', 'creation']

        for mode in valid_modes:
            # Modo creation requiere tema
            if mode == 'creation':
                args = argparse.Namespace(mode=mode, tema=['test'])
            else:
                args = argparse.Namespace(mode=mode)
            is_valid, errors = validator.validate_args(args)

            assert is_valid, f"Modo {mode} debería ser válido"

    def test_valid_all_exercise_types(self, validator):
        """Test todos los tipos de ejercicio válidos."""
        valid_types = ['development', 'multiple_choice']

        for ex_type in valid_types:
            args = argparse.Namespace(type=ex_type)
            is_valid, errors = validator.validate_args(args)

            assert is_valid, f"Tipo {ex_type} debería ser válido"

    def test_creation_mode_without_tags_warning(self, validator):
        """Test modo creation sin tags (warning)."""
        args = argparse.Namespace(
            mode='creation',
            tema=['analisis_vectorial']
        )

        is_valid, errors = validator.validate_args(args)

        assert is_valid
        assert len(validator.warnings) > 0
        assert any('tags' in warning for warning in validator.warnings)

    def test_creation_mode_without_tema_error(self, validator):
        """Test modo creation sin tema (error)."""
        args = argparse.Namespace(
            mode='creation'
        )

        is_valid, errors = validator.validate_args(args)

        assert not is_valid
        assert any('tema' in error.lower() for error in errors)

    def test_generic_api_without_base_url_warning(self, validator):
        """Test API genérica sin base_url (warning)."""
        args = argparse.Namespace(
            api='generic',
            base_path='.'
        )

        is_valid, errors = validator.validate_args(args)

        assert is_valid
        assert len(validator.warnings) > 0
        assert any('base_url' in warning for warning in validator.warnings)
