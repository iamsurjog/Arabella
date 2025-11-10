#!/usr/bin/env python3
"""
Arabella System Verification Script
Checks that all components are properly installed and configured
"""

import sys
import importlib
from pathlib import Path

def check_python_version():
    """Check Python version"""
    print("Checking Python version...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 13:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro} found")
        return True
    else:
        print(f"✗ Python 3.13+ required, found {version.major}.{version.minor}.{version.micro}")
        return False

def check_dependencies():
    """Check required Python packages"""
    print("\nChecking Python dependencies...")
    required_packages = [
        "fastapi",
        "pydantic",
        "uvicorn",
        "requests",
        "bs4",
        "ollama",
        "kuzu",
        "qdrant_client",
        "numpy",
        "nltk",
        "semchunk",
        "pytest"
    ]
    
    all_found = True
    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ✗ {package} - Not found")
            all_found = False
    
    return all_found

def check_nltk_data():
    """Check NLTK data"""
    print("\nChecking NLTK data...")
    try:
        import nltk
        required_data = ['stopwords', 'punkt']
        all_found = True
        
        for data_name in required_data:
            try:
                nltk.data.find(f'corpora/{data_name}' if data_name == 'stopwords' else f'tokenizers/{data_name}')
                print(f"  ✓ {data_name}")
            except LookupError:
                print(f"  ✗ {data_name} - Not found")
                all_found = False
        
        return all_found
    except ImportError:
        print("  ✗ NLTK not installed")
        return False

def check_directories():
    """Check required directories"""
    print("\nChecking project structure...")
    required_dirs = [
        "crawler",
        "query_bridge",
        "rag",
        "db",
        "scripts",
        "tests"
    ]
    
    all_found = True
    for dir_name in required_dirs:
        path = Path(dir_name)
        if path.exists() and path.is_dir():
            print(f"  ✓ {dir_name}/")
        else:
            print(f"  ✗ {dir_name}/ - Not found")
            all_found = False
    
    return all_found

def check_files():
    """Check required files"""
    print("\nChecking required files...")
    required_files = [
        "main.py",
        "config.yaml",
        "requirements.txt",
        "Dockerfile",
        "docker-compose.yml",
        "pytest.ini"
    ]
    
    all_found = True
    for file_name in required_files:
        path = Path(file_name)
        if path.exists() and path.is_file():
            print(f"  ✓ {file_name}")
        else:
            print(f"  ✗ {file_name} - Not found")
            all_found = False
    
    return all_found

def check_modules():
    """Check that custom modules can be imported"""
    print("\nChecking custom modules...")
    modules = [
        ("crawler", "crawl_relations"),
        ("query_bridge", "QueryBridge"),
        ("rag", "GraphRAG"),
        ("db.KuzuDB", "KuzuDB"),
        ("db.QdrantDB", "QdrantDB"),
    ]
    
    all_found = True
    for module_name, attr_name in modules:
        try:
            module = importlib.import_module(module_name)
            if hasattr(module, attr_name):
                print(f"  ✓ {module_name}.{attr_name}")
            else:
                print(f"  ✗ {module_name}.{attr_name} - Attribute not found")
                all_found = False
        except ImportError as e:
            print(f"  ✗ {module_name} - Import error: {e}")
            all_found = False
    
    return all_found

def check_ollama():
    """Check Ollama availability"""
    print("\nChecking Ollama...")
    try:
        import ollama
        # Try to list models
        models = ollama.list()
        print(f"  ✓ Ollama is accessible")
        
        # Check for required models
        required_models = ["nomic-embed-text:v1.5", "llama3.2:3b"]
        model_names = [m.get('name', '') for m in models.get('models', [])]
        
        all_models_found = True
        for model in required_models:
            if any(model in name for name in model_names):
                print(f"  ✓ {model} available")
            else:
                print(f"  ✗ {model} not found")
                all_models_found = False
        
        if not all_models_found:
            print(f"\n  To install missing models, run:")
            print(f"    make setup-ollama")
            print(f"  Or manually:")
            for model in required_models:
                if not any(model in name for name in model_names):
                    print(f"    ollama pull {model}")
        
        return all_models_found
    except Exception as e:
        print(f"  ✗ Ollama not accessible: {e}")
        print(f"  Make sure Ollama is running: ollama serve")
        print(f"  Note: Ollama is required for full functionality")
        return False

def main():
    """Run all checks"""
    print("=" * 60)
    print("Arabella System Verification")
    print("=" * 60)
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("NLTK Data", check_nltk_data),
        ("Directories", check_directories),
        ("Files", check_files),
        ("Modules", check_modules),
        ("Ollama", check_ollama),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\nError checking {name}: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{name:.<40} {status}")
    
    all_passed = all(result for _, result in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All checks passed! System is ready.")
        print("\nNext steps:")
        print("  1. Initialize databases: make init")
        print("  2. Start the application: make run")
        print("  3. Visit: http://localhost:8000/docs")
        return 0
    else:
        print("✗ Some checks failed. Please review the output above.")
        print("\nCommon fixes:")
        print("  - Install dependencies: make install")
        print("  - Install Ollama models: make setup-ollama")
        print("  - Ensure Ollama is running: ollama serve")
        print("  - Download NLTK data: included in 'make install'")
        print("  - Install Ollama: https://ollama.ai")
        return 1

if __name__ == "__main__":
    sys.exit(main())
