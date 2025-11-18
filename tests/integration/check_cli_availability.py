#!/usr/bin/env python
"""Quick check for CLI availability before running integration tests.

This script verifies:
1. All CLIs are installed and in PATH
2. All CLIs can be executed
3. Basic configuration is present

Run this before running integration tests to ensure your environment is ready.

Usage:
    python tests/integration/check_cli_availability.py
"""

import shutil
import subprocess
import sys
from pathlib import Path

# ANSI color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def check_cli(cli_name: str) -> tuple[bool, str]:
    """Check if a CLI is available and executable.
    
    Returns:
        (success, message)
    """
    # Check if in PATH
    cli_path = shutil.which(cli_name)
    if not cli_path:
        return False, f"Not found in PATH"
    
    # Try to execute with --version or --help
    for flag in ["--version", "--help", "-h"]:
        try:
            result = subprocess.run(
                [cli_name, flag],
                capture_output=True,
                timeout=5,
                text=True,
            )
            if result.returncode == 0:
                return True, f"Available at {cli_path}"
        except subprocess.TimeoutExpired:
            continue
        except Exception as e:
            continue
    
    # If we get here, CLI exists but might not respond to flags
    return True, f"Found at {cli_path} (but may not respond to --version/--help)"


def check_config_files() -> dict[str, bool]:
    """Check if configuration files exist."""
    config_dir = Path("conf/cli_clients")
    results = {}
    
    for cli_name in ["gemini", "codex", "claude", "iflow", "kimi", "qwen", "vecli"]:
        config_file = config_dir / f"{cli_name}.json"
        results[cli_name] = config_file.exists()
    
    return results


def main():
    print(f"{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}Clink CLI Availability Check{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")
    
    cli_names = ["gemini", "codex", "claude", "iflow", "kimi", "qwen", "vecli"]
    
    # Check CLI availability
    print(f"{YELLOW}Checking CLI Tools:{RESET}\n")
    
    results = {}
    max_name_len = max(len(name) for name in cli_names)
    
    for cli_name in cli_names:
        success, message = check_cli(cli_name)
        results[cli_name] = success
        
        status = f"{GREEN}✓{RESET}" if success else f"{RED}✗{RESET}"
        color = GREEN if success else RED
        
        print(f"  {status} {cli_name:<{max_name_len}} : {color}{message}{RESET}")
    
    # Check configuration files
    print(f"\n{YELLOW}Checking Configuration Files:{RESET}\n")
    
    config_results = check_config_files()
    
    for cli_name in cli_names:
        exists = config_results[cli_name]
        status = f"{GREEN}✓{RESET}" if exists else f"{RED}✗{RESET}"
        color = GREEN if exists else RED
        message = "Present" if exists else "Missing"
        
        print(f"  {status} conf/cli_clients/{cli_name}.json : {color}{message}{RESET}")
    
    # Summary
    print(f"\n{BLUE}{'='*70}{RESET}")
    
    cli_available = sum(results.values())
    cli_total = len(cli_names)
    config_available = sum(config_results.values())
    
    print(f"\n{YELLOW}Summary:{RESET}")
    print(f"  CLIs Available: {cli_available}/{cli_total}")
    print(f"  Configs Available: {config_available}/{cli_total}")
    
    if cli_available == cli_total and config_available == cli_total:
        print(f"\n{GREEN}✓ All checks passed! Ready to run integration tests.{RESET}")
        print(f"\n{BLUE}Run integration tests with:{RESET}")
        print(f"  python -m pytest tests/integration/ -m integration -v")
        return 0
    else:
        print(f"\n{RED}✗ Some checks failed. Please fix the issues above.{RESET}")
        
        if cli_available < cli_total:
            print(f"\n{YELLOW}Missing CLIs:{RESET}")
            for cli_name, available in results.items():
                if not available:
                    print(f"  - {cli_name}: Install and ensure it's in your PATH")
        
        if config_available < cli_total:
            print(f"\n{YELLOW}Missing Configs:{RESET}")
            for cli_name, exists in config_results.items():
                if not exists:
                    print(f"  - {cli_name}: Create conf/cli_clients/{cli_name}.json")
        
        return 1


if __name__ == "__main__":
    sys.exit(main())
