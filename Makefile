.PHONY: init test flake8 coverage publish

init:
	pip3 install pipenv --upgrade
	pipenv install --dev --ignore-pipfile

test:
	pipenv run nosetests

flake8:
	pipenv run flake8

coverage:
	pipenv run coveralls

publish:
	python setup.py sdist upload
