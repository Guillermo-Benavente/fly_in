VENV   := .venv
PYTHON := $(shell pwd)/$(VENV)/bin/python3
PIP    := $(shell pwd)/$(VENV)/bin/pip
MAPS   := easy/01_linear_path easy/02_simple_fork easy/03_basic_capacity \
          medium/01_dead_end_trap medium/02_circular_loop medium/03_priority_puzzle \
          hard/01_maze_nightmare hard/02_capacity_hell hard/03_ultimate_challenge \
          challenger/01_the_impossible_dream
install:
	@echo "Setting up virtual environment..."
	@python3 -m venv $(VENV)
	@echo "Install dependencies..."
	@$(PIP) install --upgrade pip > /dev/null 2>&1
	@$(PIP) install StrEnum flake8 mypy > /dev/null 2>&1
	@echo "Done."

run:
	@$(PYTHON) fly_in.py $(MAP)

debug:
	@$(PYTHON) -m pdb fly_in.py $(MAP)

clean:
	@rm -rf __pycache__ .mypy_cache output
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

lint:
	@$(VENV)/bin/mypy . --exclude='\.venv' --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs && \
	$(VENV)/bin/flake8 . --exclude=.venv,__pycache__

lint-strict:
	@$(VENV)/bin/mypy . --exclude='\.venv' --strict && \
	$(VENV)/bin/flake8 . --exclude=.venv,__pycache__

visual:
	@mkdir -p output
	@for map in $(MAPS); do \
		name=$${map##*/}; \
		echo "Generating output/$$name.html ..."; \
		$(PYTHON) visualizer.py maps/$$map.txt output/$$name.html; \
	done
	@echo "Done. HTML files in output/"

.PHONY: install run debug clean lint lint-strict visual