ifeq ($(OS),Windows_NT)
    detected_OS := Windows
    PYTHON_BIN = python.exe
    PIP_BIN = pip.exe
    ACTIVATE_CMD = activate.bat
    BIN_DIR_NAME = Scripts
else
    detected_OS := $(shell sh -c 'uname 2>/dev/null || echo Unknown')
    PYTHON_BIN = python3
    PIP_BIN = pip
    ACTIVATE_CMD = activate
    BIN_DIR_NAME = bin
endif

VENV = venv
PYTHON_BINS = $(VENV)/$(BIN_DIR_NAME)
PYTHON = $(PYTHON_BINS)/$(PYTHON_BIN)
PIP = $(PYTHON_BINS)/$(PIP_BIN)
ACTIVATE = $(PYTHON_BINS)/$(ACTIVATE_CMD)

export PYTHONPATH := $(CURDIR)/app

run: $(ACTIVATE)
	$(PYTHON) app/main.py

run-bin: dist/main
	./dist/main

format: $(ACTIVATE)
	$(PYTHON) -m isort .
	$(PYTHON) -m black --target-version py310 --skip-string-normalization --line-length 120 app

format_check: $(ACTIVATE)
	@echo "##### Check imports format #####"
	$(PYTHON) -m isort -c .

	@echo "##### Check code format #####"
	$(PYTHON) -m black --target-version py310 --skip-string-normalization --line-length 120 --check app

test_code: $(ACTIVATE)
	@echo "##### Check code tests #####"
	$(PYTHON) -m unittest discover

test: format_check test_code

coverage: $(ACTIVATE)
	$(PYTHON) -m coverage run -m unittest discover
	$(PYTHON) -m coverage report -m
	$(PYTHON) -m coverage html
	xdg-open htmlcov/index.html

$(ACTIVATE): requirements.txt dev_requirements.txt
	@echo "##### Create virtual env #####"
	pip3 install virtualenv
	python -m venv $(VENV) --clear
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
