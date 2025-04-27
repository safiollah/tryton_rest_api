## Fix: Prevent Crash in Float Field Formatting / (SAO)

- **File:** `sao/src/model.js`
- **Function:** `Sao.field.Float.digits`
- **Issue:** The code could crash with a `TypeError: Cannot read properties of undefined (reading '0')` if the `digits` configuration for a float field was invalid or could not be determined (e.g., due to a failed RPC call or incorrect model/view definition).
- **Fix:** Added a check within the `digits` function to validate that the `digits` variable is a proper array with at least two elements before attempting to access `digits[0]` or `digits[1]`. If the check fails, a warning is logged, and the function returns `undefined`, preventing the crash later when the value is formatted.

## Manual Version Downgrade to 7.4.9

- **Context:** This project's core components (`tryton`, `trytond`, `sao`) were manually reverted from version `7.5.0` to `7.4.9`.
- **Affected Files:**
    - `tryton/tryton/__init__.py` (Set `__version__ = "7.4.9"`)
    - `trytond/trytond/__init__.py` (Set `__version__ = "7.4.9"`)
    - `sao/src/sao.js` (Set `Sao.__version__ = '7.4.9'`)
    - `sao/package.json` (Set `"version": "7.4.9"`)
- **Installation Notes:**
    - **Using version 7.4.9 (Current state):** Requires local installation of the core modules. Run either the `install_local_modules.py` or `install_local_modules.sh` script located in the root of the workspace.
    - **Using version 7.5.0 (or future releases):** If you revert these changes or use a future version released on PyPI, local installation is typically not needed. You can usually install the server component directly using `pip install trytond==<version>`.


