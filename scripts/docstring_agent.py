import os
import random
import glob
from dataclasses import dataclass
from google import genai
import time

@dataclass
class Config:
    SOURCE_DIR: str = "src/femora"
    STYLE_GUIDE_PATH: str = "STYLE_GUIDE.md"
    EXTENSIONS: tuple = (".py",)

def get_random_file(source_dir: str) -> str:
    """Selects a random Python file from the source directory."""
    files = glob.glob(os.path.join(source_dir, "**/*.py"), recursive=True)
    # Filter out __init__.py and empty files if needed
    valid_files = [f for f in files if os.path.getsize(f) > 0]
    if not valid_files:
        raise FileNotFoundError("No Python files found.")
    return random.choice(valid_files)

def read_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def main():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Skipping: GEMINI_API_KEY not found.")
        return

    client = genai.Client(api_key=api_key)
    
    # 1. Load Context
    try:
        style_guide = read_file(Config.STYLE_GUIDE_PATH)
    except FileNotFoundError:
        print(f"Error: {Config.STYLE_GUIDE_PATH} not found.")
        return

    # 2. Pick a Target
    target_file = get_random_file(Config.SOURCE_DIR)
    print(f"Refactoring docstrings for: {target_file}")
    
    original_code = read_file(target_file)
    
    # 3. Prompt Engineering
    prompt = f"""
    You are an expert Python documentation engineer. Your task is to rewrite the docstrings in the following Python code to strictly adhere to the Google Style Guide provided below.

    Rules:
    1. ONLY change docstrings. Do NOT change logic or variable names.
    2. Add missing docstrings for all classes and public functions.
    3. Use the exact indentation and formatting rules from the guide.
    4. Return ONLY the full valid Python code. No markdown fences.

    Style Guide:
    {style_guide}

    Target Code:
    {original_code}
    """

    # 4. Agent Execution with Retry Logic
    models_to_try = [
        'gemini-2.5-flash',
        'gemini-2.0-flash',
        'gemini-flash-latest',
        'gemini-2.5-pro',
        'gemini-2.0-flash-001'
    ]
    
    new_code = None
    
    for model_name in models_to_try:
        print(f"Trying model: {model_name}...")
        try:
            response = client.models.generate_content(
                model=model_name, 
                contents=prompt
            )
            new_code = response.text
            print(f"Success with {model_name}!")
            break
        except Exception as e:
            print(f"Failed with {model_name}: {e}")
            
    if not new_code:
        print("ALL models failed.")
        print("DEBUG: Listing available models for this API Key:")
        try:
            for m in client.models.list():
                # Safely inspect the model object
                try:
                    name = getattr(m, 'name', 'Unknown')
                    disp = getattr(m, 'display_name', '')
                    print(f" - {name} ({disp})")
                except:
                    print(f" - {m}")
        except Exception as e2:
            print(f"Error listing models: {e2}")
        return
    
    # Clean possible markdown fences
    if new_code.startswith("```python"):
        lines = new_code.splitlines()
        # Remove first line (```python) and last line (```)
        if lines[0].strip().startswith("```"):
            lines = lines[1:]
        if lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        new_code = "\n".join(lines)
    elif new_code.startswith("```"):
         lines = new_code.splitlines()
         new_code = "\n".join(lines[1:-1])

        
    # 5. Save Changes
    with open(target_file, "w", encoding="utf-8") as f:
        f.write(new_code)
    
    print(f"Successfully updated docstrings for {target_file}")

    # Set output for GitHub Action
    if "GITHUB_OUTPUT" in os.environ:
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"refactored_file={target_file}\n")

if __name__ == "__main__":
    main()
