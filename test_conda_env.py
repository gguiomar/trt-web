#!/usr/bin/env python3
"""
Test script to verify conda environment setup and dependencies
"""

import sys
import os
import subprocess

def test_conda_environment():
    """Test if we're running in the correct conda environment"""
    print("=== Conda Environment Test ===")
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version}")
    
    # Check if we're in a conda environment
    conda_env = os.environ.get('CONDA_DEFAULT_ENV')
    if conda_env:
        print(f"✓ Running in conda environment: {conda_env}")
        if conda_env == 'vst':
            print("✓ Correct environment (vst)")
        else:
            print(f"⚠️  Expected 'vst' environment, but found '{conda_env}'")
    else:
        print("✗ Not running in a conda environment")
    
    print()

def test_dependencies():
    """Test if all required dependencies are available"""
    print("=== Dependency Test ===")
    
    dependencies = [
        'flask',
        'werkzeug', 
        'gunicorn',
        'click',
        'itsdangerous',
        'jinja2',
        'markupsafe',
        'dateutil',
        'uuid'
    ]
    
    for dep in dependencies:
        try:
            if dep == 'dateutil':
                import dateutil
            elif dep == 'uuid':
                import uuid
            else:
                __import__(dep)
            print(f"✓ {dep}")
        except ImportError as e:
            print(f"✗ {dep} - {e}")
    
    print()

def test_flask_session():
    """Test Flask-Session dependency"""
    print("=== Flask-Session Test ===")
    try:
        from flask_session import Session
        print("✓ flask-session imported successfully")
    except ImportError as e:
        print(f"✗ flask-session import failed: {e}")
    
    print()

def test_custom_modules():
    """Test if custom modules can be imported"""
    print("=== Custom Modules Test ===")
    
    custom_modules = [
        'utils.config',
        'utils.GameLogger',
        'utils.UserManager', 
        'utils.VSTtask',
        'utils.StatsCalculator'
    ]
    
    for module in custom_modules:
        try:
            __import__(module)
            print(f"✓ {module}")
        except ImportError as e:
            print(f"✗ {module} - {e}")
    
    print()

def test_gunicorn():
    """Test if gunicorn is available and working"""
    print("=== Gunicorn Test ===")
    try:
        result = subprocess.run(['gunicorn', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ Gunicorn version: {result.stdout.strip()}")
        else:
            print(f"✗ Gunicorn test failed: {result.stderr}")
    except FileNotFoundError:
        print("✗ Gunicorn not found in PATH")
    
    print()

def main():
    """Run all tests"""
    print("Testing VST Application Conda Environment Setup")
    print("=" * 50)
    print()
    
    test_conda_environment()
    test_dependencies()
    test_flask_session()
    test_custom_modules()
    test_gunicorn()
    
    print("=" * 50)
    print("Test completed!")

if __name__ == '__main__':
    main()
