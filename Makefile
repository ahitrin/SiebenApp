ENV:=.env

.PHONY: venv test run clean

all: venv

venv:
	virtualenv -p /usr/bin/python3 $(ENV)
	$(ENV)/bin/pip3 install -r requirements.txt

test:
	$(ENV)/bin/py.test

run:
	$(ENV)/bin/python sieben.py

clean:
	rm -rf $(ENV)
