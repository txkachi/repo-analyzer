#!/usr/bin/env python3
"""
Installation script for Repository Analyzer.
This script facilitates the installation of the project in development mode.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(command, description):
    """Execute a command and handle errors."""
    print(f"Executing: {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"SUCCESS: {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: {description} failed:")
        print(f"   Command: {command}")
        print(f"   Error: {e.stderr}")
        return False


def check_python_version():
    """Verify Python version compatibility."""
    if sys.version_info < (3, 11):
        print("ERROR: Python 3.11+ is required")
        print(f"   Current version: {sys.version}")
        return False
    print(f"Python version: {sys.version}")
    return True


def check_git():
    """Verify Git installation."""
    try:
        result = subprocess.run(['git', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"Git: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    
    print("ERROR: Git is not installed or not in PATH")
    print("   Please install Git from: https://git-scm.com/")
    return False


def install_dependencies():
    """Install project dependencies."""
    print("\nInstalling dependencies...")
    
    # Upgrade pip
    if not run_command(f"{sys.executable} -m pip install --upgrade pip", "Upgrading pip"):
        return False
    
    # Install the project in development mode
    if not run_command(f"{sys.executable} -m pip install -e .", "Installing Repository Analyzer"):
        return False
    
    return True


def install_dev_dependencies():
    """Install development dependencies."""
    print("\nInstalling development dependencies...")
    
    if not run_command(f"{sys.executable} -m pip install -e '.[dev]'", "Installing development dependencies"):
        print("WARNING: Development dependencies installation failed, but core installation succeeded")
        return False
    
    return True


def run_tests():
    """Execute the test suite."""
    print("\nRunning tests...")
    
    if not run_command(f"{sys.executable} -m pytest tests/ -v", "Running test suite"):
        print("WARNING: Tests failed, but installation succeeded")
        return False
    
    return True


def show_usage():
    """Display usage instructions."""
    print("\nInstallation completed successfully.")
    print("\nUsage:")
    print("   # Analyze a local repository")
    print("   repoanalyze analyze /path/to/your/repo")
    print("")
    print("   # Analyze a GitHub repository")
    print("   repoanalyze analyze https://github.com/username/repo")
    print("")
    print("   # Start web interface")
    print("   repoanalyze web")
    print("")
    print("   # Get help")
    print("   repoanalyze --help")
    print("")
    print("For more information, see README.md")


def main():
    """Main installation function."""
    print("Repository Analyzer Installation")
    print("=" * 40)
    
    # Check prerequisites
    if not check_python_version():
        sys.exit(1)
    
    if not check_git():
        sys.exit(1)
    
    # Install the project
    if not install_dependencies():
        print("\nERROR: Installation failed. Please check the error messages above.")
        sys.exit(1)
    
    # Ask about development dependencies
    print("\nInstall development dependencies (pytest, black, mypy, etc.)? [y/N]")
    try:
        response = input().strip().lower()
        if response in ['y', 'yes']:
            install_dev_dependencies()
    except KeyboardInterrupt:
        print("\nSkipping development dependencies")
    
    # Ask about running tests
    print("\nRun tests to verify installation? [y/N]")
    try:
        response = input().strip().lower()
        if response in ['y', 'yes']:
            run_tests()
    except KeyboardInterrupt:
        print("\nSkipping tests")
    
    # Show usage
    show_usage()


if __name__ == "__main__":
    main()
