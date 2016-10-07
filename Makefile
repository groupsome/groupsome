PYTHON = ../virtualenv/bin/python
COVERAGE = ../virtualenv/bin/coverage
BASE = ./messengerext
SETTINGS = config.settings_local
TEST_SETTINGS = config.settings_test

.PHONY: run startapp makemigrations migrate test coverage report html shell polltelegram stylus translation

run:
	@cd $(BASE) && (stylus -c -w static/style/main.styl & $(PYTHON) ./manage.py runserver --settings=$(SETTINGS))

startapp:
	@cd $(BASE) && $(PYTHON) ./manage.py startapp $(APPNAME)

makemigrations:
	@cd $(BASE) && $(PYTHON) ./manage.py makemigrations --settings=$(SETTINGS)

migrate:
	@cd $(BASE) && $(PYTHON) ./manage.py migrate --settings=$(SETTINGS)

test:
	@cd $(BASE) && $(PYTHON) ./manage.py collectstatic --noinput --settings=$(TEST_SETTINGS) && $(PYTHON) ./manage.py test $(APPNAME) --settings=$(TEST_SETTINGS)

coverage:
	@cd $(BASE) && $(COVERAGE) run ./manage.py test $(APPNAME) --settings=$(TEST_SETTINGS)

report:
	@cd $(BASE) && $(COVERAGE) report

html:
	@cd $(BASE) && $(COVERAGE) html

shell:
	@cd $(BASE) && $(PYTHON) ./manage.py shell --settings=$(SETTINGS)

polltelegram:
	@cd $(BASE) && $(PYTHON) ./manage.py polltelegram --settings=$(SETTINGS)

rqworker:
	@cd $(BASE) && $(PYTHON) ./manage.py rqworker --settings=$(SETTINGS)

rqscheduler:
	@cd $(BASE) && $(PYTHON) ./manage.py rqscheduler --settings=$(SETTINGS)

stylus:
	@echo "You propably don't need make stylus anymore, make run starts stylus itself"
	@cd $(BASE) && stylus -c -w static/style/main.styl &

translation_DE:
	@cd $(BASE) && $(PYTHON) ./manage.py makemessages -l de --settings=$(SETTINGS)

compile_translations:
	@cd $(BASE) && $(PYTHON) ./manage.py compilemessages --settings=$(SETTINGS)
