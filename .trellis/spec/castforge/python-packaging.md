# Python Packaging

- Support Python 3.10 or newer as declared by `pyproject.toml`.
- Build the package with the setuptools backend declared in `pyproject.toml`.
- Keep the core dependency set independent of provider-specific integrations.
- Gemini and NotebookLM are optional extras. Do not require their credentials, local state, or services for core package use or ordinary build validation.
- Treat `pyproject.toml` as the authority for package metadata, dependencies, optional extras, and build-system configuration.
