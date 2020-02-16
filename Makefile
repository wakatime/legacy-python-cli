.PHONY: init test flake8 coverage publish

init:
	pip install pyenv pipenv --upgrade
	pyenv install --skip-existing
	pipenv install --dev --ignore-pipfile

test:
	pipenv run nosetests

flake8:
	pipenv run flake8

coverage:
	pipenv run coveralls

publish:
	python setup.py sdist upload
