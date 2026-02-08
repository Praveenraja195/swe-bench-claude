import os
import sys

try:
    import anthropic
except ImportError:
    print("Please run: pip install anthropic")
    sys.exit(1)

# List of all potential model names to try
CANDIDATES = [
    "claude-3-5-sonnet-20241022", # Latest Sonnet (Oct 2024)
    "claude-3-5-sonnet-20240620", # Previous Sonnet (June 2024)
    "claude-3-5-haiku-20241022",  # Latest Haiku
    "claude-3-opus-20240229",     # Opus
    "claude-3-sonnet-20240229",   # Old Sonnet
    "claude-3-haiku-20240307",    # Old Haiku
    "claude-2.1",                 # Legacy
    "claude-2.0",                 # Legacy
    "claude-instant-1.2"          # Legacy
]

def main():
    api_key = os.environ.get('CLAUDE_API_KEY')
    if not api_key:
        print("❌ Error: CLAUDE_API_KEY is missing.")
        return

    print(f"🔑 Testing Key: {api_key[:10]}...")
    client = anthropic.Anthropic(api_key=api_key.strip())

    print("\n🚀 Starting Model Hunt...")
    
    for model in CANDIDATES:
        print(f"👉 Testing: {model.ljust(30)}", end="")
        try:
            client.messages.create(
                model=model,
                max_tokens=5,
                messages=[{"role": "user", "content": "Hi"}]
            )
            print("✅ SUCCESS! USE THIS MODEL.")
            print(f"\n🎉 WINNER: {model}")
            print(f"Update your run_agent.py with: model=\"{model}\"")
            return
        except anthropic.NotFoundError:
            print("❌ Not Found (404)")
        except anthropic.BadRequestError as e:
            print(f"❌ Bad Request: {e}")
        except Exception as e:
            print(f"❌ Error: {e}")

    print("\n❌ No working models found. Please check your API Key permissions.")

if __name__ == "__main__":
    main()