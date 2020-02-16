.PHONY: init test flake8 coverage publish

init:
	pip install pipenv --upgrade
	pipenv install --dev

test:
	pipenv run nosetests

flake8:
	pipenv run flake8

coverage:
	pipenv run coveralls

publish:
	python setup.py sdist upload
