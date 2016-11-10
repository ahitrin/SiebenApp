ENV:=.env

.PHONY: venv clean

all: venv

venv:
	virtualenv -p /usr/bin/python3 $(ENV)
	$(ENV)/bin/pip3 install -r requirements.txt

clean:
	rm -rf $(ENV)
