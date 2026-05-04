"""
Tests para ConfigValidator.
"""
import pytest
from pathlib import Path
from evolutia.validation.config_validator import ConfigValidator


class TestConfigValidator:
    """Test suite para ConfigValidator."""

    @pytest.fixture
    def validator(self):
        return ConfigValidator()

    def test_empty_config(self, validator):
        """Test configuración vacía (todos warnings)."""
        config = {}

        is_valid, errors = validator.validate_config(config)

        # Config vacía es válida (todos los campos son opcionales)
        assert is_valid
        assert len(errors) == 0
        # Debe haber warnings
        assert len(validator.warnings) > 0

    def test_valid_minimal_config(self, validator):
        """Test configuración mínima válida."""
        config = {
            'paths': {
                'base_path': str(Path.cwd())
            },
            'api': {
                'default_provider': 'openai'
            }
        }

        is_valid, errors = validator.validate_config(config)

        assert is_valid
        assert len(errors) == 0

    def test_valid_full_config(self, validator):
        """Test configuración completa válida."""
        config = {
            'paths': {
                'base_path': str(Path.cwd()),
                'materials_directories': ['analisis_vectorial', 'calculo']
            },
            'api': {
                'default_provider': 'openai',
                'providers': {
                    'openai': {
                        'model': 'gpt-4',
                        'max_tokens': 2000,
                        'temperature': 0.7
                    },
                    'local': {
                        'base_url': 'http://localhost:11434/v1',
                        'model': 'llama3'
                    }
                }
            },
            'exam': {
                'default': {
                    'subject': 'Física - II semestre 2025',
                    'points_per_exercise': 25,
                    'duration_hours': 2.0
                },
                'keywords': {
                    'analisis_vectorial': ['vector', 'integral', 'gradiente']
                }
            },
            'generation': {
                'max_workers': 5,
                'request_delay': 1.0,
                'retry_attempts': 3,
                'llm_params': {
                    'default_temperature': 0.7,
                    'default_max_tokens': 2000
                },
                'complexity': {
                    'min_improvement_percent': 10,
                    'required_improvements_count': 2
                }
            },
            'rag': {
                'vector_store': {
                    'type': 'chromadb',
                    'persist_directory': './storage/vector_store'
                },
                'embeddings': {
                    'provider': 'openai',
                    'model': 'text-embedding-3-small',
                    'batch_size': 100
                },
                'retrieval': {
                    'top_k': 5,
                    'similarity_threshold': 0.7
                },
                'chunking': {
                    'chunk_size': 1000,
                    'chunk_overlap': 100
                }
            }
        }

        is_valid, errors = validator.validate_config(config)

        assert is_valid
        assert len(errors) == 0

    def test_invalid_default_provider(self, validator):
        """Test proveedor por defecto inválido."""
        config = {
            'api': {
                'default_provider': 'invalido'
            }
        }

        is_valid, errors = validator.validate_config(config)

        assert not is_valid
        assert any('default_provider' in error.lower() for error in errors)

    def test_invalid_base_path(self, validator):
        """Test ruta base inválida."""
        config = {
            'paths': {
                'base_path': '/ruta/que/no/existe'
            }
        }

        is_valid, errors = validator.validate_config(config)

        assert not is_valid
        assert any('base_path' in error.lower() for error in errors)

    def test_invalid_openai_temperature(self, validator):
        """Test temperatura de OpenAI inválida."""
        config = {
            'api': {
                'providers': {
                    'openai': {
                        'temperature': 3.0  # Fuera de rango [0, 2]
                    }
                }
            }
        }

        is_valid, errors = validator.validate_config(config)

        assert not is_valid
        assert any('temperature' in error.lower() for error in errors)

    def test_invalid_openai_max_tokens(self, validator):
        """Test max_tokens de OpenAI inválido."""
        config = {
            'api': {
                'providers': {
                    'openai': {
                        'max_tokens': -100  # Negativo
                    }
                }
            }
        }

        is_valid, errors = validator.validate_config(config)

        assert not is_valid
        assert any('max_tokens' in error.lower() for error in errors)

    def test_invalid_local_base_url(self, validator):
        """Test base_url de local inválida."""
        config = {
            'api': {
                'providers': {
                    'local': {
                        'base_url': 'not-a-url'  # No empieza con http:// o https://
                    }
                }
            }
        }

        is_valid, errors = validator.validate_config(config)

        assert not is_valid
        assert any('base_url' in error.lower() for error in errors)

    def test_invalid_exam_duration(self, validator):
        """Test duración de examen inválida."""
        config = {
            'exam': {
                'default': {
                    'duration_hours': 30.0  # Mayor a 24
                }
            }
        }

        is_valid, errors = validator.validate_config(config)

        assert not is_valid
        assert any('duration_hours' in error.lower() for error in errors)

    def test_invalid_generation_max_workers(self, validator):
        """Test max_workers de generación inválido."""
        config = {
            'generation': {
                'max_workers': 100  # Mayor a 50
            }
        }

        is_valid, errors = validator.validate_config(config)

        assert not is_valid
        assert any('max_workers' in error.lower() for error in errors)

    def test_invalid_rag_vector_store_type(self, validator):
        """Test tipo de vector store inválido."""
        config = {
            'rag': {
                'vector_store': {
                    'type': 'invalido'
                }
            }
        }

        is_valid, errors = validator.validate_config(config)

        assert not is_valid
        assert any('type' in error.lower() and 'vector_store' in error.lower() for error in errors)

    def test_invalid_rag_embeddings_provider(self, validator):
        """Test proveedor de embeddings inválido."""
        config = {
            'rag': {
                'embeddings': {
                    'provider': 'invalido'
                }
            }
        }

        is_valid, errors = validator.validate_config(config)

        assert not is_valid
        assert any('provider' in error.lower() and 'embeddings' in error.lower() for error in errors)

    def test_invalid_rag_retrieval_top_k(self, validator):
        """Test top_k de recuperación inválido."""
        config = {
            'rag': {
                'retrieval': {
                    'top_k': 200  # Mayor a 100
                }
            }
        }

        is_valid, errors = validator.validate_config(config)

        assert not is_valid
        assert any('top_k' in error.lower() for error in errors)

    def test_invalid_rag_chunking_overlap(self, validator):
        """Test overlap de chunking inválido (mayor que chunk_size)."""
        config = {
            'rag': {
                'chunking': {
                    'chunk_size': 100,
                    'chunk_overlap': 150  # Mayor que chunk_size
                }
            }
        }

        is_valid, errors = validator.validate_config(config)

        assert not is_valid
        assert any('chunk_overlap' in error.lower() for error in errors)

    def test_invalid_exam_keywords_not_list(self, validator):
        """Test keywords de examen no es lista."""
        config = {
            'exam': {
                'keywords': {
                    'analisis_vectorial': 'not-a-list'  # Debe ser lista
                }
            }
        }

        is_valid, errors = validator.validate_config(config)

        assert not is_valid
        assert any('keywords' in error.lower() for error in errors)

    def test_valid_all_api_providers(self, validator):
        """Test todos los proveedores de API válidos."""
        valid_providers = ['openai', 'anthropic', 'local', 'gemini', 'deepseek', 'generic']

        for provider in valid_providers:
            config = {
                'api': {
                    'default_provider': provider
                }
            }

            is_valid, errors = validator.validate_config(config)

            assert is_valid, f"Provider {provider} debería ser válido"

    def test_valid_all_rag_embedding_providers(self, validator):
        """Test todos los proveedores de embeddings válidos."""
        valid_providers = ['openai', 'sentence-transformers']

        for provider in valid_providers:
            config = {
                'rag': {
                    'embeddings': {
                        'provider': provider
                    }
                }
            }

            is_valid, errors = validator.validate_config(config)

            assert is_valid, f"Provider {provider} debería ser válido"

    def test_valid_anthropic_temperature(self, validator):
        """Test temperatura de Anthropic válida (0-1)."""
        config = {
            'api': {
                'providers': {
                    'anthropic': {
                        'temperature': 0.8  # En rango [0, 1]
                    }
                }
            }
        }

        is_valid, errors = validator.validate_config(config)

        assert is_valid

    def test_invalid_anthropic_temperature(self, validator):
        """Test temperatura de Anthropic inválida (fuera de 0-1)."""
        config = {
            'api': {
                'providers': {
                    'anthropic': {
                        'temperature': 1.5  # Fuera de rango [0, 1]
                    }
                }
            }
        }

        is_valid, errors = validator.validate_config(config)

        assert not is_valid
        assert any('temperature' in error.lower() for error in errors)

    def test_warning_unknown_provider(self, validator):
        """Test warning para proveedor desconocido."""
        config = {
            'api': {
                'providers': {
                    'unknown_provider': {}
                }
            }
        }

        is_valid, errors = validator.validate_config(config)

        assert is_valid  # Es válido, pero hay warning
        assert len(validator.warnings) > 0
        assert any('unknown_provider' in warning for warning in validator.warnings)
