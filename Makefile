
PYTHON ?= python
NOSETESTS ?= nosetests

DOC_ROOT = doc
EXAMPLES = examples

.PHONY: clean
clean: doc-clean
	find . -name '*.pyc' -delete
	rm -rf coverage .coverage
	rm -rf *.egg-info

.PHONY: test
test:
	$(NOSETESTS) -s -v gerber

.PHONY: test-coverage
test-coverage:
	rm -rf coverage .coverage
	$(NOSETESTS) -s -v --with-coverage --cover-package=gerber

.PHONY: doc-html
doc-html:
	(cd $(DOC_ROOT); make html)

.PHONY: doc-clean
doc-clean:
	(cd $(DOC_ROOT); make clean)

.PHONY: examples
examples:
	PYTHONPATH=. $(PYTHON) examples/cairo_example.py
	PYTHONPATH=. $(PYTHON) examples/pcb_example.py

