ENV:=.env

.PHONY: check venv test install run clean distclean

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

install:
	PATH=$(ENV)/bin:${PATH} python3 setup.py install

run:
	PATH=$(ENV)/bin:${PATH} ./sieben

clean:
	rm -rf build
	find . -name \*.pyc -delete

distclean:
	rm -rf $(ENV)
