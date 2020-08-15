ENV:=.env

.PHONY: check venv test install lint format mypy run clean distclean prepare

all: check venv test

check:
	if [ ! `which python3` ] ; then echo Please install Python 3.5 or greater ; exit 1; fi
	if [ `python3 -V | cut -d. -f2` -lt 6 ]; then echo Please install Python 3.6 or greater; exit 1; fi
	if [ ! `which virtualenv` ] ; then echo Please install virtualenv ; exit 1; fi
	if [ ! `which dot` ] ; then echo Please install Graphviz ; exit 1; fi

venv:
	$([ which pipenv ] || pip install pipenv)
	pipenv install -d

prepare: test format lint mypy

test:
	pipenv run py.test

install:
	pipenv run python3 setup.py install

lint:
	pipenv run pylint siebenapp

format:
	pipenv run black sieben siebenapp

mypy:
	pipenv run mypy --pretty -p siebenapp

run:
	pipenv run ./sieben

clean:
	rm -rf build
	find . -name \*.pyc -delete

distclean:
	rm -rf $(ENV)
