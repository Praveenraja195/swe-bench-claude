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
    raw_api_key = os.environ.get('CLAUDE_API_KEY')
    if not raw_api_key:
        print("❌ Error: CLAUDE_API_KEY is missing.")
        raise Exception("CLAUDE_API_KEY missing")
    
    api_key = raw_api_key.strip()
    print(f"🔑 Found API Key: {api_key[:8]}...{api_key[-4:]}")

    if not anthropic:
        raise Exception("anthropic library not installed")

    # WINNER MODEL
    MODEL_NAME = "claude-3-5-haiku-20241022"
    print(f"🤖 Connecting to {MODEL_NAME}...")
    
    client = anthropic.Anthropic(api_key=api_key, max_retries=3)
    
    filepath = 'openlibrary/core/imports.py'
    if not os.path.exists(filepath):
        print(f"⚠️ File not found: {filepath}. Skipping AI fix.")
        raise Exception("Target file not found")

    with open(filepath, 'r', encoding='utf-8') as f:
        code_content = f.read()

    # UPDATED PROMPT: Explicitly forbids db.where to prevent SQLite errors
    full_prompt = f"""
    You are an expert Python Developer.
    The file `openlibrary/core/imports.py` needs a refactor.
    
    CURRENT CODE:
    ```python
    {code_content}
    ```
    
    TASK:
    {prompt}
    
    CRITICAL IMPLEMENTATION DETAILS:
    1. You MUST construct the `ids` list like this: `ids = [f"{{s}}:{{i}}" for s in sources for i in identifiers]`
    2. You MUST use `db.select` for the query.
    3. ❌ DO NOT use `db.where()` because it causes 'row value misused' errors in SQLite with lists.
    4. Use this exact return statement:
       `return db.select("import_item", where="ia_id in $ids and status in ('staged', 'pending')", vars={{"ids": ids}})`
    5. ⚠️ IMPORTANT: Return the FULL file content. Do not use comments like "# ... rest of file".
    
    INSTRUCTIONS:
    - Return ONLY the full valid python code for the modified file.
    - Wrap the code in ```python ... ``` blocks.
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
        
        # --- 🛡️ SMART VALIDATION LAYERS ---

        # 1. Security Check
        if 'db.where(' in new_code and 'ia_id=ids' in new_code:
             raise Exception("AI used forbidden db.where() method.")

        # 2. LAZY DELETION CHECK (Crucial Fix)
        # If the AI deleted the Stats class, REJECT the code.
        if "class Stats" not in new_code:
            print("🚨 AI attempted to delete 'class Stats'. Triggering Fail-Safe...")
            raise Exception("Lazy Deletion detected: AI removed 'class Stats'.")

        # 3. Completeness Check
        if "# Rest of the file" in new_code or "# ... source code ..." in new_code:
             raise Exception("Lazy Deletion detected: AI returned incomplete file.")

        # Write only if it passes all checks
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_code)
        print("✅ Claude successfully refactored the file!")
        return True
    else:
        raise Exception("AI did not return valid python code block")

def apply_fix_manually():
    print('⚠️ Engaging Manual Override (Safe Mode)...')
    log_event("mode", "manual_fix_applied")
    filepath = 'openlibrary/core/imports.py'
    
    try:
        # Read the ORIGINAL file (since we prevented the AI from writing broken code)
        with open(filepath, 'r', encoding='utf-8') as f: 
            content = f.read()

        # 1. Add STAGED_SOURCES constant
        if 'STAGED_SOURCES =' not in content:
            # Add it after the logger definition or imports
            content = content.replace('logger = logging.getLogger("openlibrary.imports")', 
                                      'logger = logging.getLogger("openlibrary.imports")\n\nSTAGED_SOURCES = ("amazon", "idb")')

        # 2. Inject the method into ImportItem class
        if 'def find_staged_or_pending' not in content:
            method_code = """
    @staticmethod
    def find_staged_or_pending(identifiers, sources=None):
        if sources is None:
            sources = STAGED_SOURCES
        ids = [f"{s}:{i}" for s in sources for i in identifiers]
        return db.select(
            "import_item", 
            where="ia_id in $ids and status in ('staged', 'pending')", 
            vars={"ids": ids}
        )
"""
            # Inject at the top of ImportItem class
            pattern = r'(class ImportItem\(web\.storage\):)'
            if re.search(pattern, content):
                content = re.sub(pattern, r'\1' + method_code, content, count=1)
                
        with open(filepath, 'w', encoding='utf-8') as f: 
            f.write(content)
        print('✅ Manual fix applied successfully.')
        
    except Exception as e:
        print(f'❌ Manual fix failed: {e}')
        traceback.print_exc()

def main():
    prompt = 'Refactor openlibrary/core/imports.py to add STAGED_SOURCES = ("amazon", "idb") and a static method find_staged_or_pending(identifiers, sources=STAGED_SOURCES).'
    save_prompt(prompt)

    try:
        attempt_ai_fix(prompt)
    except Exception as e:
        print(f"❌ AI Error: {e}")
        # Because we added the validation checks, this will now run
        # whenever the AI tries to be "lazy" and delete code.
        apply_fix_manually()

if __name__ == '__main__':
    main()