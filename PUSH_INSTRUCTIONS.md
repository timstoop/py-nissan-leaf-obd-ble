# Push this repo to GitHub

This directory is a standalone Git repo for **py-nissan-leaf-obd-ble**. The main repo (nissan-leaf-obd-ble) no longer contains this package and depends on the PyPI package instead.

1. **Create the repo on GitHub**  
   Create a new repository named `py-nissan-leaf-obd-ble` (e.g. https://github.com/pbutterworth/py-nissan-leaf-obd-ble). Do **not** add a README, .gitignore, or license.

2. **Push this repo** (origin is already set):
   ```bash
   cd _new_package_repo
   git push -u origin main
   ```
   If you use a different GitHub URL, update the remote first:
   ```bash
   git remote set-url origin https://github.com/YOUR_USER/py-nissan-leaf-obd-ble.git
   git push -u origin main
   ```

3. **Optional: move this folder** out of the main repo (e.g. to `../py-nissan-leaf-obd-ble`) so you have two separate project directories. The main repo ignores `_new_package_repo/` via `.gitignore`.

4. **Publish to PyPI** when ready (from this repo):
   ```bash
   pip install build twine
   python -m build
   twine upload dist/*
   ```
