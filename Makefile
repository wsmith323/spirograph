ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
PYTHON := $(if $(VIRTUAL_ENV),$(VIRTUAL_ENV)/bin/python,$(HOME)/work/virtualenvs/spirograph/bin/python)

test:
	$(PYTHON) -m pytest -q

test-verbose:
	$(PYTHON) -m pytest -v

test-generation:
	$(PYTHON) -m pytest $(ROOT)/tests/spirograph/generation/test_circular_generator.py -q
