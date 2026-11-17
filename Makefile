# dev-pocket-tools — developer convenience targets
# Run `make help` for a list of available targets.

PYTHON ?= python

.PHONY: test lint help clean

## test: run the full unittest suite with verbose output
test:
	$(PYTHON) -m unittest discover -s tests -v

## lint: byte-compile every source tree to catch syntax errors
lint:
	$(PYTHON) -m compileall -q tools bin tests

## clean: remove Python bytecode caches and build artifacts
clean:
	$(PYTHON) -c "import pathlib, shutil; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('__pycache__')]; [p.unlink() for p in pathlib.Path('.').rglob('*.py[co]') if p.is_file()]"

## help: show this target list
help:
	@echo "dev-pocket-tools — available targets"
	@echo ""
	@echo "  test    Run the unittest suite (python -m unittest discover -s tests -v)"
	@echo "  lint    Byte-compile tools, bin and tests (python -m compileall -q tools bin tests)"
	@echo "  clean   Remove __pycache__ directories and .pyc/.pyo files"
	@echo "  help    Show this help message"
	@echo ""
	@echo "Usage: make <target>   e.g. make test"
