# Nexora AI Documentation

This directory contains the Sphinx documentation for the Nexora AI project, focusing on the API v1 endpoints.

## Setup

1. Install the documentation dependencies:

   ```bash
   uv sync
   ```

2. Navigate to the docs directory:
   ```bash
   cd docs
   ```

## Building Documentation

### Build HTML Documentation

```bash
make html
```

The built documentation will be available in `_build/html/index.html`.

### Other Build Formats

```bash
make latexpdf  # Build PDF documentation
make epub      # Build EPUB documentation
make doctest   # Run doctests
make linkcheck # Check external links
```

### Clean Build

```bash
make clean
```

## Development

### Auto-rebuild Documentation

For development, you can use `sphinx-autobuild` to automatically rebuild docs when files change:

```bash
pip install sphinx-autobuild
sphinx-autobuild . _build/html
```

Then open http://localhost:8000 in your browser.

### Adding New Documentation

1. **API Endpoints**: Add new endpoint documentation in `api/v1/endpoints/`
2. **Modules**: Run `sphinx-apidoc` to auto-generate module documentation:
   ```bash
   sphinx-apidoc -o . ../src
   ```

## Documentation Structure

```
docs/
├── index.rst                 # Main documentation page
├── api/                      # API documentation
│   ├── index.rst            # API overview
│   └── v1/                  # API v1 documentation
│       ├── index.rst        # v1 overview
│       └── endpoints/       # Individual endpoint docs
│           ├── chat.rst
│           ├── conversations.rst
│           ├── health.rst
│           ├── voice.rst
│           └── moderation.rst
├── modules.rst              # Auto-generated module docs
├── conf.py                  # Sphinx configuration
├── Makefile                 # Build commands (Unix)
└── make.bat                 # Build commands (Windows)
```

## Features

- **API Documentation**: Comprehensive documentation for all v1 endpoints
- **Auto-generated Module Docs**: Python docstring documentation
- **Code Examples**: Practical usage examples for each endpoint
- **Cross-references**: Links between related documentation
- **Search**: Full-text search functionality
- **Mobile-friendly**: Responsive design that works on all devices

## Viewing Documentation

After building, open `_build/html/index.html` in your web browser to view the documentation.

## Contributing

When adding new API endpoints or modifying existing ones:

1. Update the corresponding `.rst` file in `api/v1/endpoints/`
2. Add code examples and usage instructions
3. Update the main index files if needed
4. Test the build with `make html`
5. Check for any warnings or errors in the build output
