.PHONY: init test flake8 coverage publish build

init:
	pipenv install --dev --ignore-pipfile

test:
	pipenv run pytest

flake8:
	pipenv run flake8

coverage:
	pipenv run coveralls

build:
	pipenv run python ./build_standalone.py

publish:
	python setup.py sdist upload
