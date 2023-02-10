# Build freakble.
build:
    @poetry build

# Remove build artifacts.
[linux]
[macos]
clean:
    @rm -rf dist/

# Remove build artifacts.
[linux]
[macos]
set-version version:
    @echo 'Setting version to {{version}}…'
    @sed -i 's/version = ".*"/version = "{{version}}"/' pyproject.toml
    @sed -i 's/__version__ = ".*"/__version__ = "{{version}}"/' src/freakble/__init__.py
