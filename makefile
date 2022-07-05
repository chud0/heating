VENV = venv
PYTHON = $(VENV)/bin/python3
PIP = $(VENV)/bin/pip

export PYTHONPATH := $(CURDIR)/app

run: $(VENV)/bin/activate
	$(PYTHON) app.py

$(VENV)/bin/activate: requirements.txt dev_requirements.txt
	python3 -m venv $(VENV)
	$(PIP) install -r requirements.txt
	$(PIP) install -r dev_requirements.txt

format: $(VENV)/bin/activate
	$(PYTHON) -m unittest discover

test: $(VENV)/bin/activate
	$(PYTHON) -m unittest discover

coverage: $(VENV)/bin/activate
	coverage run -m unittest discover
	coverage report -m
	coverage html
	xdg-open htmlcov/index.html

clean: clean-pyc clean-test

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test:
	rm -f .coverage
	rm -f coverage.xml
	rm -fr htmlcov/