.PHONY: check venv test test-cov test-prop-ci analysis install format codestyle mypy run clean distclean prepare

all: check venv test

check:
	if [ ! `which python3` ] ; then echo Please install Python 3.10 or greater ; exit 1; fi
	if [ `python3 -V | cut -d. -f2` -lt 10 ]; then echo Please install Python 3.10 or greater; exit 1; fi
	if [ ! `which poetry` ] ; then echo Please install poetry ; exit 1; fi

venv:
	poetry install

prepare: codestyle format test mypy

test:
	poetry run pytest

test-cov:
	poetry run pytest --cov=siebenapp --cov-report=html

test-prop-ci: export HYPOTHESIS_PROFILE=ci
test-prop-ci:
	poetry run pytest -k test_properties

analysis:
	poetry run radon cc -nc -s siebenapp/*.py

codestyle:
	find siebenapp -type f -name \*.py | grep -v ui | xargs poetry run pyupgrade --py310-plus

format:
	poetry run black siebenapp tests

mypy:
	poetry run mypy --pretty -p siebenapp
	poetry run mypy --pretty -p tests

run:
	poetry run sieben

clean:
	find . -name \*.pyc -delete
	rm -rf build dist
