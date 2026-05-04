
import pytest
from unittest.mock import patch
from pathlib import Path
import sys
import yaml

# Add project root to path
sys.path.insert(0, str(Path(__file__).parents[1]))

from evolutia.config_manager import ConfigManager
import evolutia_cli

@pytest.fixture
def temp_project(tmp_path):
    """Creates a temporary project structure."""
    # Create topic directories
    (tmp_path / "tema1").mkdir()
    (tmp_path / "tema2").mkdir()
    (tmp_path / "ignored_dir").mkdir()
    
    # Create markdown files
    (tmp_path / "tema1" / "lectura.md").write_text("---\nkeywords: [math, physics]\n---\nContent", encoding="utf-8")
    (tmp_path / "tema2" / "practica.md").write_text("Just content", encoding="utf-8")
    (tmp_path / "ignored_dir" / "ignored.md").write_text("Ignored", encoding="utf-8")
    
    return tmp_path

def test_discover_topics(temp_project):
    """Test that topics are correctly discovered based on directories with .md files."""
    # Only verify logic, mock EXCLUDED_DIRS if necessary, but here we can just use defaults
    # assuming 'ignored_dir' is NOT in the default excluded list in source, 
    # but we should check what IS excluded.
    
    # Let's mock EXCLUDED_DIRS in the class instance scope if possible, or just rely on default.
    # In config_manager.py, EXCLUDED_DIRS is a module level set.
    # For this test, let's assume 'tema1' and 'tema2' are valid topics.
    
    manager = ConfigManager(base_path=temp_project)
    topics = manager.discover_topics()
    
    assert "tema1" in topics
    assert "tema2" in topics
    # We didn't set 'ignored_dir' in excluded, so it should be there unless we mock it.
    assert "ignored_dir" in topics 

def test_extract_keywords(temp_project):
    """Test keyword extraction from frontmatter."""
    manager = ConfigManager(base_path=temp_project)
    keywords = manager.extract_keywords_from_topic("tema1")
    assert "math" in keywords
    assert "physics" in keywords
    
    keywords_empty = manager.extract_keywords_from_topic("tema2")
    assert keywords_empty == []

def test_update_config_creates_file(temp_project):
    """Test that update_config creates a config file."""
    config_path = temp_project / "evolutia_config.yaml"
    manager = ConfigManager(base_path=temp_project, config_path=config_path)
    
    manager.update_config()
    
    assert config_path.exists()
    
    with open(config_path) as f:
        config = yaml.safe_load(f)
        
    assert "tema1" in config['paths']['materials_directories']
    assert "math" in config['exam']['keywords']['tema1']

def test_cli_analyze_argument(temp_project):
    """Test that the CLI accepts --analyze and calls the manager."""
    with patch('evolutia_cli.ConfigManager') as MockManager:
        with patch('sys.argv', ['evolutia', '--analyze']):
            # Mock the instance
            instance = MockManager.return_value
            
            # Run main
            with patch('evolutia_cli.Path.cwd', return_value=temp_project):
                 ret = evolutia_cli.main()
                 
            assert ret == 0
            # Verify alias was called
            instance.update_config_from_structure.assert_called_once()
