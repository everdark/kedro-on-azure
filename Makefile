FILE_PATH = ./src

.PHONY: lint
lint:
	@black $(FILE_PATH)
	@isort --profile black $(FILE_PATH)
	@flake8 --max-line-length 88 --extend-ignore=E203 $(FILE_PATH)
	@bandit -r $(FILE_PATH) --exclude ./src/tests
