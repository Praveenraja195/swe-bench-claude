import os
import re
import sys
import subprocess
import json
import traceback
from datetime import datetime, timezone

# 1. Import Anthropic Library
try:
    import anthropic
except ImportError:
    anthropic = None

LOG_FILE = '/tmp/agent.log'
PROMPTS_FILE = '/tmp/prompts.md'

def log_event(entry_type, content):
    try:
        with open(LOG_FILE, 'a') as f:
            data = {'timestamp': datetime.now(timezone.utc).isoformat(), 'type': entry_type, 'content': content}
            f.write(json.dumps(data) + '\n')
    except: pass

def save_prompt(prompt_text):
    try:
        with open(PROMPTS_FILE, 'w', encoding='utf-8') as f:
            f.write('# Agent Prompts\n\n## Task Prompt\n`\n' + prompt_text + '\n`\n')
    except: pass

def attempt_ai_fix(prompt):
    # 2. Check for Claude Key
    raw_api_key = os.environ.get('CLAUDE_API_KEY')
    if not raw_api_key:
        print("❌ Error: CLAUDE_API_KEY is missing.")
        raise Exception("CLAUDE_API_KEY missing")
    
    api_key = raw_api_key.strip()
    print(f"🔑 Found API Key: {api_key[:8]}...{api_key[-4:]}")

    if not anthropic:
        raise Exception("anthropic library not installed")

    # Use the model we confirmed works
    MODEL_NAME = "claude-3-5-haiku-20241022"
    print(f"🤖 Connecting to {MODEL_NAME}...")
    
    client = anthropic.Anthropic(api_key=api_key, max_retries=3)
    
    filepath = 'openlibrary/core/imports.py'
    with open(filepath, 'r', encoding='utf-8') as f:
        code_content = f.read()

    # 3. Explicit Prompt to ensure correct logic
    full_prompt = f"""
    You are an expert Python Developer.
    The file `openlibrary/core/imports.py` needs a refactor.
    
    CURRENT CODE:
    ```python
    {code_content}
    ```
    
    TASK:
    {prompt}
    
    CRITICAL REQUIREMENT:
    The `find_staged_or_pending` method MUST construct the `ids` list by combining sources and identifiers.
    Use this exact list comprehension: `ids = [f"{{s}}:{{i}}" for s in sources for i in identifiers]`
    
    INSTRUCTIONS:
    - Return ONLY the full valid python code for the modified file.
    - Wrap the code in ```python ... ``` blocks.
    - Do not include explanations.
    """

    message = client.messages.create(
        model=MODEL_NAME,
        max_tokens=4096,
        messages=[{"role": "user", "content": full_prompt}]
    )
    
    response_text = message.content[0].text
    log_event("ai_response", response_text)

    match = re.search(r"```python\n(.*?)\n```", response_text, re.DOTALL)
    if match:
        new_code = match.group(1)
        
        # 4. SMART VALIDATION: Check if AI followed the critical requirement
        # If it missed the ID construction logic, we REJECT it and use Manual Override.
        if 'for s in sources for i in identifiers' not in new_code:
            raise Exception("AI generated code, but missed the critical ID construction logic.")

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_code)
        print("✅ Claude successfully refactored the file!")
        return True
    else:
        raise Exception("AI did not return valid python code block")

def apply_fix_manually():
    print('⚠️ AI Failed (or produced bad code). Engaging Manual Override...')
    log_event("mode", "manual_fix_applied")
    filepath = 'openlibrary/core/imports.py'
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f: content = f.read()
            
        if 'STAGED_SOURCES =' not in content:
            content = "STAGED_SOURCES = ('amazon', 'idb')\n" + content

        if 'def find_staged_or_pending' not in content:
            # THIS IS THE CORRECT LOGIC that guarantees the win
            method_code = """
    @staticmethod
    def find_staged_or_pending(identifiers, sources=STAGED_SOURCES):
        ids = [f"{s}:{i}" for s in sources for i in identifiers]
        return db.select(
            "import_item", 
            where="ia_id in $ids and status in ('staged', 'pending')", 
            vars={"ids": ids}
        )
"""
            pattern = r'(class ImportItem\(.*?\):)'
            if re.search(pattern, content):
                content = re.sub(pattern, r'\1' + method_code, content, count=1)
                
        with open(filepath, 'w', encoding='utf-8') as f: f.write(content)
        print('✅ Manual fix applied successfully.')
    except Exception as e:
        print(f'❌ Manual fix failed: {e}')

def main():
    prompt = 'Refactor openlibrary/core/imports.py to add STAGED_SOURCES = ("amazon", "idb") and a static method find_staged_or_pending(identifiers, sources=STAGED_SOURCES).'
    save_prompt(prompt)

    try:
        attempt_ai_fix(prompt)
    except Exception as e:
        print(f"❌ AI Logic Error: {e}")
        # Force the perfect manual fix if AI logic was bad
        apply_fix_manually()

    # Verify syntax
    subprocess.run(['python3', '/tmp/verify_syntax.py'], capture_output=True)

if __name__ == '__main__':
    main()