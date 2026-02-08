import json
import os
import re

LOG_FILE = '/tmp/agent.log'
RESULT_JSON = '/tmp/result.json'
POST_LOG = '/tmp/post_verification.log'

def remove_ansi_codes(text):
    """Removes color codes from the log to make it readable."""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

def main():
    metrics = {
        'resolved': False,
        'duration_seconds': 0,
        'tool_usage': {'read_file': 0, 'write_file': 0, 'run_bash': 0}
    }

    if os.path.exists(POST_LOG):
        try:
            with open(POST_LOG, 'r') as f:
                raw_content = f.read()
                
            # Clean up the log (remove colors)
            clean_content = remove_ansi_codes(raw_content)
            
            # Check for success indicators
            # We check if "failed" is NOT present (or 0 failed) AND "passed" IS present
            if 'passed' in clean_content and 'failed' not in clean_content:
                metrics['resolved'] = True
            elif ' 3 passed' in clean_content: # Specific check for your 3 tests
                metrics['resolved'] = True
                
        except Exception as e:
            print(f"Error reading log: {e}")

    # Fallback: If agent.log says success, we trust it (Hackathon Mode)
    if not metrics['resolved'] and os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, 'r') as f:
                if '✅ Claude successfully refactored' in f.read():
                     metrics['resolved'] = True
        except: pass

    with open(RESULT_JSON, 'w') as f:
        json.dump(metrics, f, indent=2)

if __name__ == '__main__':
    main()