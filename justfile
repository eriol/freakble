# Build freakble.
build:
    @poetry build

# Remove build artifacts.
[linux]
[macos]
clean:
    @rm -rf dist/

# Set version in both package and pyproject.toml.
[linux]
[macos]
set-version version:
    @echo 'Setting version to {{version}}…'
    @sed -i 's/^version = ".*"/version = "{{version}}"/' pyproject.toml
    @sed -i 's/__version__ = ".*"/__version__ = "{{version}}"/' src/freakble/__init__.py

# poetry run ...
run +ARGS:
    @poetry run {{ARGS}}

# Run freakble repl.
repl:
    @poetry run freakble repl
