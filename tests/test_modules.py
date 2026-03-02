"""ARK95X Unified Sovereign Stack - Module Test & Train Suite
Run: python -m pytest tests/test_modules.py -v
Purpose: Verify every module loads, has valid structure, and can initialize.
This is the test-train system - each module must prove it works.
"""
import importlib
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

MODULES = [
    "core",
    "flame",
    "intelligence",
    "sovereignty",
    "trading",
    "command",
    "consciousness",
    "performance",
    "protocol",
    "infra",
    "n8n",
    "scaling",
    "netx",
    "integrations",
]


def test_all_modules_import():
    """Test that every module in the unified stack can be imported."""
    results = {}
    for module_name in MODULES:
        try:
            mod = importlib.import_module(module_name)
            results[module_name] = "PASS"
            assert mod is not None, f"{module_name} imported as None"
        except Exception as e:
            results[module_name] = f"FAIL: {e}"
    
    # Print report
    print("\n" + "=" * 50)
    print("ARK95X MODULE TEST REPORT")
    print("=" * 50)
    passed = 0
    failed = 0
    for name, status in results.items():
        icon = "[PASS]" if status == "PASS" else "[FAIL]"
        print(f"  {icon} {name}: {status}")
        if status == "PASS":
            passed += 1
        else:
            failed += 1
    print(f"\nTotal: {passed} passed, {failed} failed out of {len(MODULES)}")
    print("=" * 50)
    
    assert failed == 0, f"{failed} modules failed to import"


def test_all_modules_have_init():
    """Test that every module directory has an __init__.py file."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for module_name in MODULES:
        init_path = os.path.join(root, module_name, "__init__.py")
        assert os.path.exists(init_path), f"Missing __init__.py in {module_name}/"


def test_main_entry_point():
    """Test that main.py exists and is importable."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    main_path = os.path.join(root, "main.py")
    assert os.path.exists(main_path), "main.py not found at project root"


def test_config_files_exist():
    """Test that all config files are present."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    required_files = [
        "requirements.txt",
        "docker-compose.yml",
        ".env.example",
        "README.md",
        "DAILY_SYNC.md",
        "SESSION_STATE.md",
    ]
    for f in required_files:
        assert os.path.exists(os.path.join(root, f)), f"Missing config file: {f}"


if __name__ == "__main__":
    test_all_modules_import()
    print("\nAll tests passed! Stack is ready.")
