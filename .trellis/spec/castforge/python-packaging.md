# Python Packaging

- Support Python 3.10 or newer as declared by `pyproject.toml`.
- Build the package with the setuptools backend declared in `pyproject.toml`.
- Keep the core dependency set independent of provider-specific integrations. YAML configuration is core; `PyYAML` is therefore a core dependency.
- Gemini, NotebookLM/browser, and R2/boto3 are optional extras. Do not require their credentials, local state, or services for core package use or ordinary build validation.
- The `test` extra owns offline pytest only. Live providers remain outside the ordinary suite.
- Treat `pyproject.toml` as the authority for package metadata, dependencies, optional extras, and build-system configuration.
