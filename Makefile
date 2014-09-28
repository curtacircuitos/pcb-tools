
PYTHON ?= python
NOSETESTS ?= nosetests


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
	
