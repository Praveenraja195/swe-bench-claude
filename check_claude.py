import os
import sys

try:
    import anthropic
except ImportError:
    print("❌ Error: 'anthropic' library not installed.")
    print("Run: pip install anthropic")
    sys.exit(1)

def main():
    # 1. Get Key
    api_key = os.environ.get('CLAUDE_API_KEY')
    if not api_key:
        print("❌ Error: CLAUDE_API_KEY environment variable is missing.")
        return

    print(f"🔑 Found API Key: {api_key[:8]}...{api_key[-4:]}")
    
    # 2. Connect
    try:
        client = anthropic.Anthropic(api_key=api_key.strip())
        print("✅ Connection established.")
    except Exception as e:
        print(f"❌ Connection Failed: {e}")
        return

    # 3. Test a Simple Message (Sanity Check)
    print("\n🧪 Testing 'claude-3-5-sonnet-latest'...")
    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=10,
            messages=[{"role": "user", "content": "Hello"}]
        )
        print("✅ Success! 'claude-3-5-sonnet-latest' IS working.")
        print(f"🤖 Response: {message.content[0].text}")
    except anthropic.NotFoundError:
        print("❌ Failed: 'claude-3-5-sonnet-latest' not found.")
        
        # 4. Fallback Test
        print("\n🧪 Testing 'claude-3-opus-20240229' (Fallback)...")
        try:
            message = client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=10,
                messages=[{"role": "user", "content": "Hello"}]
            )
            print("✅ Success! 'claude-3-opus-20240229' IS working.")
        except Exception as e:
            print(f"❌ Fallback Failed: {e}")

    except Exception as e:
        print(f"❌ Critical Error: {e}")

if __name__ == "__main__":
    main()


