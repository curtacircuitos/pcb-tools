
PYTHON ?= python
NOSETESTS ?= nosetests

DOC_ROOT = doc

clean:
	#$(PYTHON) setup.py clean
	find . -name '*.pyc' -delete
	rm -rf coverage .coverage
	rm -rf *.egg-info
test:
	$(NOSETESTS) -s -v gerber
	
test-coverage:
	rm -rf coverage .coverage
	$(NOSETESTS) -s -v --with-coverage gerber
	
doc-html:
	(cd $(DOC_ROOT); make html)

       
doc-clean:
	(cd $(DOC_ROOT); make clean)
	

