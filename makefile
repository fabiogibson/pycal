.PHONY: all
all: pycal


.PHONY: clean 
clean:
	@rm -f ./dist/pycal
	@rm -f /usr/local/bin/pycal

pycal: check test pycal/main.py
	@pipenv run pyinstaller --onefile pycal/main.py -n pycal

.PHONY: install
install:
	@ln -s $(CURDIR)/dist/pycal /usr/local/bin/pycal

check:
	@pipenv run black .
	@pipenv run flake8 .
	@pipenv run mypy .

test:
	@pipenv run pytest --cov=pycal --cov-report=html

run:
	@pipenv run python -m pycal.main agenda
