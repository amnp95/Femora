import os
import shutil
import subprocess
import http.server
import socketserver
import webbrowser
import sys

# --- CONFIGURATION ---
ROOT_DIR = os.getcwd()
WEBSITE_DIR = os.path.join(ROOT_DIR, 'website')
TEST_DIR = os.path.join(ROOT_DIR, '_local_test')
NEXTJS_BUILD_OUTPUT = os.path.join(WEBSITE_DIR, 'out') # Next.js default export folder
PORT = 8000

def print_step(message):
    print(f"\n{'='*60}")
    print(f"👉 {message}")
    print(f"{'='*60}")

def check_prerequisites():
    """Checks if output: 'export' is configured in Next.js"""
    config_path = os.path.join(WEBSITE_DIR, 'next.config.mjs')
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if "output: 'export'" not in content and 'output: "export"' not in content:
                print("❌ ERROR: Your next.config.mjs is missing `output: 'export'`.")
                print("   Please add it to the config object so Next.js creates HTML files.")
                sys.exit(1)

def install_node_deps():
    """Installs npm packages if node_modules is missing."""
    node_modules = os.path.join(WEBSITE_DIR, 'node_modules')
    if not os.path.exists(node_modules):
        print_step("Installing Node.js dependencies (First time only)...")
        subprocess.run("npm install", cwd=WEBSITE_DIR, shell=True, check=True)
    else:
        print("✅ Node modules already installed.")

def build_nextjs():
    """Builds the Next.js website into static HTML."""
    print_step("Building Next.js Landing Page...")
    
    # Run the build command
    try:
        # shell=True is required for Windows to find 'npm'
        subprocess.run("npm run build", cwd=WEBSITE_DIR, shell=True, check=True)
    except subprocess.CalledProcessError:
        print("❌ Next.js Build Failed.")
        print("   Run 'npm run build' inside the website folder to see the error.")
        sys.exit(1)

    # Verify the output exists
    if not os.path.exists(NEXTJS_BUILD_OUTPUT):
        print(f"❌ Error: The 'out' folder was not created at {NEXTJS_BUILD_OUTPUT}.")
        print("   Did you save the changes to next.config.mjs?")
        sys.exit(1)

def prepare_test_folder():
    """Copies the Next.js build to the test folder."""
    print_step("Preparing Local Test Folder...")
    
    if os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR)
    
    # Copy the 'out' folder (Next.js HTML) to '_local_test'
    shutil.copytree(NEXTJS_BUILD_OUTPUT, TEST_DIR)
    print(f"✅ Website copied to {TEST_DIR}")

def build_mkdocs():
    """Builds MkDocs into the subfolder of the test site."""
    print_step("Building Documentation...")
    
    mkdocs_config = os.path.join(WEBSITE_DIR, "mkdocs.yml")
    output_dir = os.path.join(TEST_DIR, "docs") # The subfolder
    
    cmd = [
        "mkdocs", "build",
        "--config-file", mkdocs_config,
        "--site-dir", output_dir
    ]
    
    try:
        subprocess.run(cmd, shell=True, check=True)
        print("✅ Documentation built successfully!")
    except subprocess.CalledProcessError:
        print("❌ MkDocs Build Failed.")
        sys.exit(1)

def serve():
    """Serves the final combined site."""
    print_step(f"🚀 Launching Server at http://localhost:{PORT}")
    
    os.chdir(TEST_DIR)
    url = f"http://localhost:{PORT}"
    
    # Open browser automatically
    webbrowser.open(url)
    
    Handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        try:
            print("   (Press Ctrl+C to stop the server)")
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server stopped.")

if __name__ == "__main__":
    check_prerequisites()
    install_node_deps()
    build_nextjs()
    prepare_test_folder()
    build_mkdocs()
    serve()