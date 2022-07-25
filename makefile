VENV = venv
PYTHON = $(VENV)/bin/python3
PIP = $(VENV)/bin/pip

export PYTHONPATH := $(CURDIR)/app

run: $(VENV)/bin/activate
	$(PYTHON) app.py

format: $(VENV)/bin/activate
	$(PYTHON) -m isort .
	$(PYTHON) -m black --target-version py310 --skip-string-normalization --line-length 120 app

format_check: $(VENV)/bin/activate
	@echo "##### Check imports format #####"
	$(PYTHON) -m isort -c .

	@echo "##### Check code format #####"
	$(PYTHON) -m black --target-version py310 --skip-string-normalization --line-length 120 --check app

test_code: $(VENV)/bin/activate
	@echo "##### Check code tests #####"
	$(PYTHON) -m unittest discover

test: format_check test_code

coverage: $(VENV)/bin/activate
	$(PYTHON) -m coverage run -m unittest discover
	$(PYTHON) -m coverage report -m
	$(PYTHON) -m coverage html
	xdg-open htmlcov/index.html

$(VENV)/bin/activate: requirements.txt dev_requirements.txt
	@echo "##### Create virtual env #####"
	python3 -m venv $(VENV)
	@echo "##### Install requirements #####"
	$(PIP) install -r requirements.txt
	$(PIP) install -r dev_requirements.txt

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