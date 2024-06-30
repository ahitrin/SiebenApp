.PHONY: check venv test test-cov test-prop-ci analysis install format codestyle mypy run clean distclean prepare

all: check venv test

check:
	if [ ! `which python3` ] ; then echo Please install Python 3.9 or greater ; exit 1; fi
	if [ `python3 -V | cut -d. -f2` -lt 9 ]; then echo Please install Python 3.9 or greater; exit 1; fi
	if [ ! `which pipenv` ] ; then echo Please install pipenv ; exit 1; fi

venv:
	$([ which pipenv ] || pip install pipenv)
	pipenv install -d --python $(shell which python3)

prepare: codestyle format test mypy

test:
	pipenv run py.test

test-cov:
	pipenv run py.test --cov=siebenapp --cov-report=html

test-prop-ci: export HYPOTHESIS_PROFILE=ci
test-prop-ci:
	pipenv run py.test -k test_properties

analysis:
	pipenv run radon cc -nc -s siebenapp/*.py

install:
	pipenv run python3 setup.py install

codestyle:
	find siebenapp -type f -name \*.py | grep -v ui | xargs pipenv run pyupgrade --py39-plus

format:
	pipenv run black sieben siebenapp clieben sieben-manage

mypy:
	pipenv run mypy --pretty -p siebenapp

run:
	pipenv run ./sieben

clean:
	find . -name \*.pyc -delete

distclean:
	pipenv --rm
