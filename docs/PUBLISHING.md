# Publishing ProfileFusion to PyPI

Follow this checklist to publish a new release of `profilefusion` to PyPI.

### 1. Build

Generate the source distribution (`.tar.gz`) and the built distribution (`.whl`).
```bash
python -m build
```

### 2. Check

Validate the package metadata using twine to ensure PyPI will accept it.
```bash
twine check dist/*
```

### 3. TestPyPI upload

Upload the build artifacts to TestPyPI to verify the process.
```bash
twine upload --repository testpypi dist/*
```

### 4. Install from TestPyPI

Verify that the package can be installed and works properly.
```bash
pip install \
--index-url https://test.pypi.org/simple/ \
profilefusion
```

### 5. Production upload

If the TestPyPI verification is successful, upload the package to the official PyPI repository.
```bash
twine upload dist/*
```
