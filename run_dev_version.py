# Script to run the current development version of zen-mcp-server using uvx
# This ensures Claude Code uses the current development version instead of a cached one

import subprocess
import sys
import os
from pathlib import Path

def main():
    """
    Run the current development version of zen-mcp-server.
    This script should be executed from the project root directory.
    """
    # Get the directory where this script is located (project root)
    project_root = Path(__file__).parent.resolve()
    server_path = project_root / "server.py"
    
    # Check if we're in the correct directory
    if not server_path.exists():
        print(f"Error: server.py not found at {server_path}")
        print("Please run this script from the zen-mcp-server project root directory")
        sys.exit(1)
    
    # Use the current Python interpreter to run the server
    # This ensures we use the current development code
    try:
        print(f"Running zen-mcp-server from: {server_path}")
        print(f"Project root: {project_root}")
        
        # Change to project directory to ensure proper module resolution
        os.chdir(project_root)
        
        # Run the server using the current Python environment
        result = subprocess.run([sys.executable, str(server_path)] + sys.argv[1:])
        sys.exit(result.returncode)
        
    except KeyboardInterrupt:
        print("\nServer stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error running server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()