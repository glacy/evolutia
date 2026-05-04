
import sys
import unittest
from pathlib import Path

# Add project root to path
# Add project root to path if needed (implicit in pytest usually, but good for safety)
sys.path.insert(0, str(Path(__file__).parent.parent))

from evolutia.utils.json_parser import extract_and_parse_json

class TestJsonParser(unittest.TestCase):
    
    def test_clean_json(self):
        """Test simple valid JSON."""
        input_text = '{"key": "value"}'
        result = extract_and_parse_json(input_text)
        self.assertEqual(result, {"key": "value"})

    def test_json_in_markdown(self):
        """Test JSON inside markdown code blocks."""
        input_text = """Here is the json:
```json
{
    "q": "simple"
}
```
Thanks."""
        result = extract_and_parse_json(input_text)
        self.assertEqual(result, {"q": "simple"})

    def test_latex_backslashes_simple(self):
        """Test LaTeX backslash handling (single backslash in string)."""
        # This is invalid JSON technically, but common LLM output for latex
        # Input string representation: '{"math": "\frac{1}{2}"}'
        # If passed as python raw string:
        input_text = r'{"math": "\frac{1}{2}"}' 
        
        result = extract_and_parse_json(input_text)
        # Expect parser to fix valid latex commands
        # Note: json parser might yield "\\frac{1}{2}" or just "\frac{1}{2}" depending on repair
        # Our repair doubles the backslash, so json.loads sees "\\frac", which decodes to "\frac"
        self.assertIsNotNone(result)
        self.assertEqual(result.get("math"), r"\frac{1}{2}")

    def test_valid_json_escapes_preserved(self):
        """Ensure valid escapes like \n and \" are NOT double escaped."""
        input_text = r'{"text": "line1\nline2", "quote": "\"hello\""}'
        result = extract_and_parse_json(input_text)
        self.assertEqual(result.get("text"), "line1\nline2")
        self.assertEqual(result.get("quote"), "\"hello\"")

    def test_mixed_latex_and_escapes(self):
        """Test mixed robust scenario."""
        input_text = r'{"math": "\textbf{Hello}", "lines": "A\nB"}'
        result = extract_and_parse_json(input_text)
        self.assertEqual(result.get("math"), r"\textbf{Hello}")
        self.assertEqual(result.get("lines"), "A\nB")

if __name__ == '__main__':
    unittest.main()
