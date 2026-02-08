import os
import re
import sys
import subprocess
import json
from datetime import datetime, timezone

try:
    import anthropic
except ImportError:
    anthropic = None

LOG_FILE = '/tmp/agent.log'
FILE_PATH = 'openlibrary/core/imports.py'

def log_event(entry_type, content):
    try:
        with open(LOG_FILE, 'a') as f:
            data = {'timestamp': datetime.now(timezone.utc).isoformat(), 'type': entry_type, 'content': content}
            f.write(json.dumps(data) + '\n')
    except: pass

def attempt_ai_fix(prompt):
    api_key = os.environ.get('CLAUDE_API_KEY')
    if not api_key: raise Exception("CLAUDE_API_KEY missing")
    if not anthropic: raise Exception("anthropic library missing")

    # Using the specific Sonnet 4.5 identifier
    MODEL_NAME = "claude-sonnet-4-5-20250929"

    print(f"🤖 Initializing {MODEL_NAME}...")
    client = anthropic.Anthropic(api_key=api_key)

    with open(FILE_PATH, 'r', encoding='utf-8') as f: 
        code_content = f.read()

    full_prompt = f"""
    You are an expert Python Developer.
    The file {FILE_PATH} needs a refactor.
    CURRENT CODE:
    python
    {code_content}
    
    TASK:
    {prompt}
    INSTRUCTIONS:
    - Return ONLY the full valid python code for the modified file.
    - Wrap the code in python ... blocks.
    """

    try:
        # Sonnet 4.5 supports enhanced tool use and reasoning
        message = client.messages.create(
            model=MODEL_NAME,
            max_tokens=4096,
            messages=[{"role": "user", "content": full_prompt}]
        )
        response_text = message.content[0].text
    except Exception as e:
        # Catching specific error details for manual fallback
        raise Exception(f"API Error ({type(e).__name__}): {str(e)}")

    log_event("ai_response", response_text)

    # Use a more robust regex for the markdown block
    match = re.search(r"python\n(.*?)\n", response_text, re.DOTALL)
    if match:
        with open(FILE_PATH, 'w', encoding='utf-8') as f: 
            f.write(match.group(1).strip())
        print(f"✅ {MODEL_NAME} successfully refactored the file!")
        return True
    else:
        raise Exception("AI Error: Code block not found in response.")

def apply_fix_manually(error):
    print(f'❌ AI Failed ({error}). Engaging Manual Override...')
    log_event("mode", "manual_fix_applied")
    try:
        with open(FILE_PATH, 'r', encoding='utf-8') as f: 
            content = f.read()
        
        # Inject constants and methods via regex
        if 'STAGED_SOURCES =' not in content:
            content = "STAGED_SOURCES = ('amazon', 'idb')\n" + content
        if 'def find_staged_or_pending' not in content:
            method_code = """
    @staticmethod
    def find_staged_or_pending(identifiers, sources=STAGED_SOURCES):
        ids = [f"{s}:{i}" for s in sources for i in identifiers]
        return db.select("import_item", where="ia_id in $ids and status in ('staged', 'pending')", vars={"ids": ids})
"""
            pattern = r'(class\s+ImportItem\(.*?\):)'
            if re.search(pattern, content):
                content = re.sub(pattern, r'\1' + method_code, content, count=1)
        
        with open(FILE_PATH, 'w', encoding='utf-8') as f: 
            f.write(content)
        print('✅ Manual fix applied successfully.')
    except Exception as e:
        print(f'❌ Manual fix failed: {e}')

def main():
    prompt = 'Refactor openlibrary/core/imports.py to add STAGED_SOURCES = ("amazon", "idb") and a static method find_staged_or_pending(identifiers, sources=STAGED_SOURCES) that returns a db.select query using "ia_id in $ids".'
    try:
        attempt_ai_fix(prompt)
    except Exception as e:
        apply_fix_manually(e)
    
    # Final syntax validation
    subprocess.run(['python3', '-m', 'py_compile', FILE_PATH])

if __name__ == '__main__':
    main()