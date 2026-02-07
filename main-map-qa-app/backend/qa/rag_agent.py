"""
RAG Agent: Retrieval-Augmented Generation for Geometry Fix Suggestions.
Uses local training_data.json as knowledge base and calls LLM for code generation.
"""
import json
import os
from typing import Optional, Dict, Any, List

# Path to training data
TRAINING_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "training_data.json")

# --------------------------------------------------
# RAG Agent Class
# --------------------------------------------------
class RAGAgent:
    def __init__(self, llm_api_key: Optional[str] = None):
        """
        Initialize the RAG Agent.
        
        Args:
            llm_api_key: API key for LLM (OpenAI/Groq/DeepSeek compatible).
                         If None, uses mock responses.
        """
        self.api_key = llm_api_key or os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")
        self.base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
        self.model_name = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
        
        self.training_data = self._load_training_data()
        self.client = None
        
        if self.api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url
                )
            except ImportError:
                pass
    
    def _load_training_data(self) -> List[Dict]:
        """Load training examples from local JSON file."""
        if os.path.exists(TRAINING_DATA_PATH):
            try:
                with open(TRAINING_DATA_PATH, "r") as f:
                    return json.load(f)
            except:
                pass
        return []
    
    def _save_training_data(self):
        """Save training examples to local JSON file."""
        try:
            with open(TRAINING_DATA_PATH, "w") as f:
                json.dump(self.training_data, f, indent=2)
        except Exception as e:
            print(f"Failed to save training data: {e}")
    
    def retrieve_fix_examples(self, error_type: str) -> List[Dict]:
        """
        Retrieve relevant past fixes for a given error type.
        Simple keyword matching (can be enhanced with embeddings later).
        """
        relevant = []
        for item in self.training_data:
            if error_type.lower() in item.get("error_type", "").lower():
                relevant.append(item)
        return relevant[:3]  # Return top 3 matches
    
    def generate_fix_suggestion(self, error: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a fix suggestion for the given error using RAG + LLM.
        
        Args:
            error: The error dictionary from geometry_qa.
            
        Returns:
            Dict with 'suggestion', 'code', and 'source' keys.
        """
        error_type = error.get("type", "Unknown")
        description = error.get("description", "")
        location = error.get("location", "")
        
        # Step 1: Retrieve relevant past fixes
        past_fixes = self.retrieve_fix_examples(error_type)
        
        # Step 2: Construct prompt
        prompt = self._build_prompt(error, past_fixes)
        
        # Step 3: Call LLM or return mock
        if self.client:
            return self._call_llm(prompt, error_type)
        else:
            return self._mock_response(error_type, past_fixes)
    
    def _build_prompt(self, error: Dict, past_fixes: List[Dict]) -> str:
        """Build the prompt for the LLM."""
        prompt = f"""You are a GIS Python expert. Fix the following map geometry error.

ERROR DETAILS:
- Type: {error.get('type')}
- Description: {error.get('description')}
- Location: {error.get('location')}
- WKT: {error.get('wkt', 'N/A')}

"""
        if past_fixes:
            prompt += "KNOWLEDGE BASE (How similar errors were fixed before):\n"
            for i, fix in enumerate(past_fixes, 1):
                prompt += f"{i}. {fix.get('user_fix_description', 'Unknown fix')}\n"
                prompt += f"   Code: {fix.get('fix_code_template', '')}\n"
        
        prompt += """
OUTPUT: Write a Python code snippet to fix this error.
Only output the code, no explanations.
"""
        return prompt
    
    def _call_llm(self, prompt: str, error_type: str) -> Dict[str, Any]:
        """Call the LLM API (supports OpenRouter/DeepSeek/Llama)."""
        try:
            messages = [
                {"role": "user", "content": f"You are a GIS Python expert. {prompt}\n\nOutput ONLY the Python code to fix this, nothing else."}
            ]
            
            # Adjust parameters for standard chat models (non-reasoning)
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=500,
                temperature=0.2,
                extra_headers={
                    "HTTP-Referer": "https://axes-systems-qa.local",
                    "X-Title": "Axes Systems QA Tool"
                }
            )
            
            # Standard chat completion response
            message = response.choices[0].message
            code = ""
            
            if hasattr(message, 'content') and message.content:
                code = message.content.strip()
            
            # Check for reasoning if using deepseek-reasoner
            if not code and hasattr(message, 'reasoning_content') and message.reasoning_content:
                # Extract code from reasoning if main content is empty
                reasoning = message.reasoning_content
                if "```python" in reasoning:
                    parts = reasoning.split("```python")
                    if len(parts) > 1:
                        code = parts[-1].split("```")[0].strip()
            
            # Clean up code if wrapped in markdown
            if code.startswith("```python"):
                code = code[9:]
            if code.startswith("```"):
                code = code[3:]
            if code.endswith("```"):
                code = code[:-3]
            code = code.strip()
            
            if not code:
                raise ValueError("Empty response from LLM")
            
            # Simple heuristic to determine fix type from code content
            fix_type = "OTHER"
            code_lower = code.lower()
            
            # Check for each strategy keyword
            if "snap" in code_lower or "nearest" in code_lower:
                fix_type = "SNAP"
            elif "delete" in code_lower or "remove" in code_lower or "drop" in code_lower:
                fix_type = "DELETE"
            elif "simplify" in code_lower or "curvature" in code_lower or "douglas" in code_lower:
                fix_type = "SIMPLIFY"
            elif "buffer" in code_lower and ("0" in code_lower or "self" in code_lower or "intersect" in code_lower):
                fix_type = "BUFFER"
            elif "make_valid" in code_lower or "is_valid" in code_lower or "repair" in code_lower:
                fix_type = "MAKE_VALID"
            elif "close" in code_lower or "ring" in code_lower or "polygon" in code_lower:
                fix_type = "CLOSE"
            elif "reverse" in code_lower or "winding" in code_lower or "orient" in code_lower:
                fix_type = "REVERSE"
            elif "densify" in code_lower or "interpolate" in code_lower:
                fix_type = "DENSIFY"
            elif "split" in code_lower:
                fix_type = "SPLIT"
            
            return {
                "suggestion": f"AI-generated fix using {self.model_name}",
                "code": code,
                "fix_type": fix_type,
                "source": "llm",
                "model": self.model_name
            }
        except Exception as e:
            # Fallback to template
            code = self._get_template_fix(error_type)
            return {
                "suggestion": f"Using template fix (API error: {str(e)[:50]})",
                "code": code,
                "source": "template"
            }
    
    def _get_template_fix(self, error_type: str) -> str:
        """Return template fix code for common error types."""
        error_lower = error_type.lower()
        if "dangle" in error_lower:
            return '''# Fix Dangle: Snap endpoint to nearest vertex
from shapely.ops import snap
from shapely.geometry import Point

def fix_dangle(line, all_lines, tolerance=1.0):
    """Snap dangling endpoint to nearest geometry."""
    start = Point(line.coords[0])
    end = Point(line.coords[-1])
    
    for other in all_lines:
        if other != line:
            snapped = snap(line, other, tolerance)
            if snapped != line:
                return snapped
    return line

# Apply: fixed_line = fix_dangle(broken_line, lines_data)'''
        elif "short" in error_lower:
            return '''# Fix Short Segment: Remove or merge
def fix_short_segment(line, min_length=2.0):
    """Remove segments shorter than min_length."""
    if line.length < min_length:
        return None  # Mark for removal
    return line

# Apply: Filter out None values from result'''
        else:
            return '''# Generic geometry fix
from shapely.validation import make_valid

def fix_geometry(geom):
    """Make geometry valid."""
    if not geom.is_valid:
        return make_valid(geom)
    return geom'''
    
    def _mock_response(self, error_type: str, past_fixes: List[Dict]) -> Dict[str, Any]:
        """Return a mock response when no API key is available."""
        if past_fixes:
            fix = past_fixes[0]
            return {
                "suggestion": fix.get("user_fix_description", "Apply standard fix"),
                "code": fix.get("fix_code_template", "# No code available"),
                "source": "rag_local"
            }
        
        # Generic responses
        if "dangle" in error_type.lower():
            return {
                "suggestion": "Snap the endpoint to the nearest vertex",
                "code": "# geometry.coords[-1] = (nearest_x, nearest_y)",
                "source": "mock"
            }
        elif "short" in error_type.lower():
            return {
                "suggestion": "Remove the short segment",
                "code": "# del lines_data[geometry_index]",
                "source": "mock"
            }
        else:
            return {
                "suggestion": "Manual review recommended",
                "code": "# No automatic fix available",
                "source": "mock"
            }
    
    def save_fix(self, error_type: str, context: str, fix_description: str, fix_code: str):
        """
        Save a user-approved fix to the training data for future RAG retrieval.
        This is the "Active Learning" component.
        """
        new_example = {
            "error_type": error_type,
            "context": context,
            "user_fix_description": fix_description,
            "fix_code_template": fix_code
        }
        self.training_data.append(new_example)
        self._save_training_data()
        return {"status": "saved", "total_examples": len(self.training_data)}


# --------------------------------------------------
# Code Sanitization (Safety Check)
# --------------------------------------------------
DANGEROUS_IMPORTS = ["os", "subprocess", "sys", "shutil", "socket", "http"]
DANGEROUS_CALLS = ["exec", "eval", "open", "import", "__import__"]

def sanitize_code(code: str) -> Dict[str, Any]:
    """
    Basic safety check for generated code.
    Returns dict with 'is_safe' and 'reason'.
    """
    code_lower = code.lower()
    
    for imp in DANGEROUS_IMPORTS:
        if f"import {imp}" in code_lower or f"from {imp}" in code_lower:
            return {"is_safe": False, "reason": f"Dangerous import detected: {imp}"}
    
    for call in DANGEROUS_CALLS:
        if f"{call}(" in code_lower:
            return {"is_safe": False, "reason": f"Dangerous function call detected: {call}"}
    
    return {"is_safe": True, "reason": "Code passed safety checks"}


# --------------------------------------------------
# Singleton Instance
# --------------------------------------------------
_agent_instance = None

def get_rag_agent() -> RAGAgent:
    """Get or create the RAG agent singleton."""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = RAGAgent()
    return _agent_instance
