# Outbreak Ripple: one command to verify everything is `make check` (SDD 10.9).
# Each target can also be run alone, for example `make unit` or `make butterfly`.

PY ?= python3
PYTEST = $(PY) -m pytest -q

.PHONY: check lint typecheck sizes content coupling unit determinism isolation causality \
        counterfactual conservation sanity butterfly balance build ui report serve golden clean

check: lint typecheck sizes content coupling unit determinism isolation causality \
       counterfactual conservation sanity butterfly balance build ui report
	@echo "make check: ALL PASSED"

lint:
	$(PY) -m ruff check .

typecheck:
	$(PY) -m mypy

sizes:
	$(PY) -m tools.check_sizes

content:
	$(PY) -m tools.validate_content

coupling:
	$(PY) -m tools.gen_coupling --check

unit:
	$(PYTEST) tests/unit

determinism:
	$(PYTEST) tests/invariants/test_determinism.py

isolation:
	$(PYTEST) tests/invariants/test_stream_isolation.py

causality:
	$(PYTEST) tests/invariants/test_causality.py

counterfactual:
	$(PYTEST) tests/invariants/test_counterfactual.py

conservation:
	$(PYTEST) tests/invariants/test_conservation.py

sanity:
	$(PYTEST) tests/invariants/test_model_sanity.py

butterfly:
	$(PYTEST) tests/invariants/test_butterfly.py

balance:
	$(PYTEST) tests/invariants/test_balance.py

build:
	$(PY) -m tools.build_web

ui: build
	node tests/ui/smoke.mjs > reports/ui_output.txt || (cat reports/ui_output.txt; exit 1)
	@echo "UI smoke test passed (details in reports/ui.json and reports/performance.json)"

report:
	$(PY) -m tools.quality_report

serve: build
	$(PY) -m tools.serve 8000

golden:
	$(PY) -m tools.update_golden

clean:
	rm -rf dist reports .pytest_cache .mypy_cache .ruff_cache
