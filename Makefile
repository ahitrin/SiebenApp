ENV:=.env

.PHONY: check venv test install run clean distclean

all: check venv test

check:
	if [ ! `which python3` ] ; then echo Please install Python 3.5 or greater ; exit 1; fi
	if [ `python3 -V | cut -d. -f2` -lt 5 ]; then echo Please install Python 3.5 or greater; exit 1; fi
	if [ ! `which virtualenv` ] ; then echo Please install virtualenv ; exit 1; fi
	if [ ! `which dot` ] ; then echo Please install Graphviz ; exit 1; fi

venv:
	virtualenv -p python3.5 $(ENV)
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
