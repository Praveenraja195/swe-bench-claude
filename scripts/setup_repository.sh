#!/bin/bash
set -e
echo "🚀 Setting up Controller Environment..."

# 1. Clean Slate (Safety for Re-runs)
rm -rf /testbed
mkdir -p /testbed

# 2. Clone OpenLibrary (Hackathon Requirement)
echo "Cloning OpenLibrary..."
git clone https://github.com/internetarchive/openlibrary.git /testbed
cd /testbed

# --- ⚠️ CRITICAL: Set the BASE Commit ---
git reset --hard 84cc4ed5697b83a849e9106a09bfed501169cc20

# 3. FORCE REMOVE SYMLINKS (Fixes "File Exists" errors)
rm -rf infogami
rm -rf infobase

# 4. BUILD THE DEEP MOCK STRUCTURE (Fixes "ImportError")
mkdir -p infogami/infobase/tests
mkdir -p infogami/utils/view
mkdir -p infogami/infobase/client
mkdir -p infogami/infobase/utils
mkdir -p psycopg2

# 5. POPULATE WITH SUPER-GREEDY MOCKS
cat <<EOF > mock_greedy.py
import sys

class Greedy:
    def __getattr__(self, name): return self
    def __call__(self, *args, **kwargs): return self
    def __iter__(self): return iter([])
    def __str__(self): return ""
    def __getitem__(self, key): return self

def __getattr__(name): return Greedy()

stats = Greedy()
safeint = Greedy()
SafeInt = Greedy()
search = Greedy()
memcache = Greedy()
Client = Greedy()
UniqueViolation = Greedy()

def parse_datetime(s): return s
def safe_str(s): return str(s)
def render_template(*args, **kwargs): return ""
def template(*args, **kwargs): return ""
EOF

# Copy mocks to satisfy all imports
cp mock_greedy.py infogami/__init__.py
cp mock_greedy.py infogami/infobase/__init__.py
cp mock_greedy.py infogami/infobase/utils/__init__.py
cp mock_greedy.py infogami/utils/__init__.py
cp mock_greedy.py infogami/utils/view/__init__.py
cp mock_greedy.py infogami/infobase/client/__init__.py
cp mock_greedy.py infogami/infobase/tests/pytest_wildcard.py
cp mock_greedy.py memcache.py
cp mock_greedy.py psycopg2/__init__.py
cp mock_greedy.py psycopg2/errors.py

# 6. CREATE SYNTAX VALIDATOR (Helper tool)
cat <<EOF > /tmp/verify_syntax.py
import py_compile
import sys
try:
    py_compile.compile('openlibrary/core/imports.py', doraise=True)
    print("✅ SYNTAX OK")
except Exception as e:
    print(f"❌ SYNTAX ERROR: {e}")
    sys.exit(1)
EOF

# 7. Restore Test File (Hackathon Requirement)
git checkout c4eebe6677acc4629cb541a98d5e91311444f5d4 -- openlibrary/tests/core/test_imports.py

# --- 🆕 ADDED: Generate the Diff Artifact ---
# The judges want to see a 'changes.patch' file. 
# We create an empty one now, and the workflow will update it after the agent runs.
touch changes.patch

echo "✅ Setup complete. Database mocked. Ready for Agent."