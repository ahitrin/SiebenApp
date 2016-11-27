ENV:=.env

.PHONY: check venv test run rescue clean

all: check venv test

check:
	if [ ! `which python3` ] ; then echo Please install Python3 ; exit 1; fi
	if [ ! `which virtualenv` ] ; then echo Please install virtualenv ; exit 1; fi
	if [ ! `which dot` ] ; then echo Please install Graphviz ; fi

venv:
	virtualenv -p /usr/bin/python3 $(ENV)
	$(ENV)/bin/pip3 install -r requirements.txt

test:
	PATH=$(ENV)/bin:${PATH} py.test

run:
	PATH=$(ENV)/bin:${PATH} python3 sieben.py

rescue:
	PATH=$(ENV)/bin:${PATH} python3 -c "import system; system.rescue_db()"

clean:
	rm -rf $(ENV)
	find . -name \*.pyc -delete
