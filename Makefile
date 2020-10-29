.PHONY: check venv test install lint format mypy run clean distclean prepare

all: check venv test

check:
	if [ ! `which python3` ] ; then echo Please install Python 3.7 or greater ; exit 1; fi
	if [ `python3 -V | cut -d. -f2` -lt 7 ]; then echo Please install Python 3.7 or greater; exit 1; fi
	if [ ! `which pipenv` ] ; then echo Please install pipenv ; exit 1; fi

venv:
	$([ which pipenv ] || pip install pipenv)
	pipenv install -d

prepare: test format lint mypy

test:
	pipenv run py.test

test-cov:
	pipenv run py.test --cov=siebenapp --cov-report=html

install:
	pipenv run python3 setup.py install

lint:
	pipenv run pylint siebenapp sieben clieben

format:
	pipenv run black sieben siebenapp clieben

mypy:
	pipenv run mypy --pretty -p siebenapp

run:
	pipenv run ./sieben

clean:
	find . -name \*.pyc -delete

distclean:
	pipenv --rm
