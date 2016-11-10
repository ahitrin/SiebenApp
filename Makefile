ENV:=.env

.PHONY: venv run clean

all: venv

venv:
	virtualenv -p /usr/bin/python3 $(ENV)
	$(ENV)/bin/pip3 install -r requirements.txt

run:
	$(ENV)/bin/python sieben.py

clean:
	rm -rf $(ENV)
