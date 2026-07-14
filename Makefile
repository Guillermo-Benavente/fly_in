VENV   := .venv
PYTHON := $(shell pwd)/$(VENV)/bin/python3
PIP    := $(shell pwd)/$(VENV)/bin/pip
install:
	@echo "Setting up virtual environment..."
	@python3 -m venv $(VENV)
	@echo "Install dependencies..."
	@$(PIP) install --upgrade pip > /dev/null 2>&1
	@$(PIP) install pydantic flake8 mypy > /dev/null 2>&1
	@$(PIP) install -r requirements.txt
	@echo "Done."
run:
	@$(PYTHON) fly_in.py

debug:
	@$(PYTHON) -m pdb fly_in.py

clean:
	@rm -rf __pycache__ .mypy_cache 
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

lint:
	@$(VENV)/bin/mypy . --exclude='\.venv' --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs && \
	$(VENV)/bin/flake8 . --exclude=.venv,__pycache__

lint-strict:
	@$(VENV)/bin/mypy . --exclude='\.venv' --strict && \
  	$(VENV)/bin/flake8 . --exclude=.venv,__pycache__

.PHONY: install run debug clean lint lint-strict