test:
	python3 -m pytest -q

test-generation:
	python3 -m pytest tests/spirograph/generation/test_circular_generator.py -q

test-verbose:
	python3 -m pytest -v
