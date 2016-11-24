ENV:=.env

.PHONY: check venv test run clean

all: check venv test

check:
	if [ ! `which python3` ] ; then echo Please install Python3 ; exit 1; fi
	if [ ! `which virtualenv` ] ; then echo Please install virtualenv ; exit 1; fi
	if [ ! `which dot` ] ; then echo Please install Graphviz ; fi

venv:
	virtualenv -p /usr/bin/python3 $(ENV)
	$(ENV)/bin/pip3 install -r requirements.txt

test:
	$(ENV)/bin/py.test

run:
	$(ENV)/bin/python sieben.py

clean:
	rm -rf $(ENV)
	find . -name \*.pyc -delete
