#!/usr/bin/env python
"""
Script to run the Tryton REST API tests
"""
import os
import sys
import unittest
import importlib.util

# Path to the test_rest.py file
TEST_FILE_PATH = r"C:\Users\miraj\Documents\MTech\tryton\restapi\venv\Lib\site-packages\trytond\tests\test_rest.py"

def run_tryton_tests():
    print("Running Tryton REST API tests...")
    
    # Load the module dynamically
    spec = importlib.util.spec_from_file_location("test_rest", TEST_FILE_PATH)
    test_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(test_module)
    
    # Discover and run tests
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(test_module)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print(f"\nTests complete: {result.testsRun} tests run")
    if result.errors:
        print(f"Errors: {len(result.errors)}")
    if result.failures:
        print(f"Failures: {len(result.failures)}")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tryton_tests()
    sys.exit(0 if success else 1) 