import json
import os

LOG_FILE = '/tmp/agent.log'
RESULT_JSON = '/tmp/result.json'
POST_LOG = '/tmp/post_verification.log'

def main():
    metrics = {'resolved': False, 'duration_seconds': 0, 'tool_usage': {'read_file': 0, 'write_file': 0, 'run_bash': 0}}

    if os.path.exists(POST_LOG):
        try:
            with open(POST_LOG, 'r') as f:
                content = f.read()
                if '3 passed' in content:
                    metrics['resolved'] = True
        except: pass

    with open(RESULT_JSON, 'w') as f:
        json.dump(metrics, f, indent=2)

if __name__ == '__main__':
    main()