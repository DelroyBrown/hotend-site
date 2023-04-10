SHELL := /bin/bash
verbosity=1

help:
	@echo "Usage:"
	@echo " make help           -- display this help"
	@echo " make install        -- install requirements and set up the database"
	@echo " make test           -- run tests"
	@echo " make run            -- run production-monitor at 127.0.0.1:8000"
	@echo " make run-external   -- run production-monitor at 0.0.0.0:8000"
	@echo " make local-token    -- create a `local_token` API auth token for a user without one. DO NOT USE IN PRODUCTION"

install_psql:
	# this is probably incomplete
	sudo apt install -y postgresql postgresql-contrib
	sudo service postgresql start
	# sudo -u postgres createuser {username}
	# createdb

install_psql14:
	sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
	wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
	sudo apt -y update
	sudo apt -y install postgresql-14
	sudo service postgresql start

install:
	# pip install -r requirements.txt
	if [ `psql -t -c "SELECT COUNT(1) FROM pg_catalog.pg_database WHERE datname = 'production_monitor'"` -eq 0 ]; then \
		psql  -c "CREATE DATABASE production_monitor"; \
	fi
	# python manage.py migrate
	#python manage.py createsuperuser

install-local: install
	pip install -r requirements_dev.txt

install-web-interface:
	#npm install
	npm run dev

test:
	@DEBUG=1 TEST_MODE=1 python manage.py test --keepdb --verbosity=$(verbosity)

run:
	@DEBUG=1 python manage.py runserver

run-external:
	sudo service postgresql start
	@DEBUG=1 python manage.py runserver 0.0.0.0:8000

make local-token:
	@python manage.py create_local_token

graph_schema:
	python manage.py graph_models -a -g -o schema.png

lint:
	@echo "Running Python linter..."
	@flake8 .
	@echo "Running Javascript linter and fixing simple errors..."
	@yarn run eslint . --fix

restore:
	if [ `psql -t -c "SELECT COUNT(1) FROM pg_catalog.pg_database WHERE datname = 'production_monitor'"` -ne 0 ]; then \
		psql  -c "DROP DATABASE production_monitor"; \
		psql  -c "CREATE DATABASE production_monitor"; \
	fi
	pg_restore --verbose --clean --no-acl --no-owner --superuser super -h localhost -d production_monitor latest.dump

get_backup:
	heroku pg:backups:download -a e3d-production-monitor
