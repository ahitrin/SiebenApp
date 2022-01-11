.PHONY: check venv test install format mypy run clean distclean prepare

all: check venv test

check:
	if [ ! `which python3` ] ; then echo Please install Python 3.8 or greater ; exit 1; fi
	if [ `python3 -V | cut -d. -f2` -lt 8 ]; then echo Please install Python 3.8 or greater; exit 1; fi
	if [ ! `which pipenv` ] ; then echo Please install pipenv ; exit 1; fi

venv:
	$([ which pipenv ] || pip install pipenv)
	pipenv install -d

prepare: test format mypy

test:
	pipenv run py.test

test-cov:
	pipenv run py.test --cov=siebenapp --cov-report=html

install:
	pipenv run python3 setup.py install

format:
	pipenv run black sieben siebenapp clieben sieben_dpg

mypy:
	pipenv run mypy --pretty -p siebenapp

run:
	pipenv run ./sieben

clean:
	find . -name \*.pyc -delete

distclean:
	pipenv --rm
