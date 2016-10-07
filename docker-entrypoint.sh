#!/bin/sh
set -e

if [ "$1" = "runserver" ]; then
	while ! mysqladmin ping -hdb --silent; do
		sleep 1
	done

	cd /app/messengerext
	
	echo "export TELEGRAM_BOT_USERNAME=$TELEGRAM_BOT_USERNAME" >> /environment.sh
	echo "export TELEGRAM_TOKEN=$TELEGRAM_TOKEN" >> /environment.sh
	echo "export MYSQL_PASSWORD=$MYSQL_PASSWORD" >> /environment.sh
	
	python manage.py collectstatic --noinput
	python manage.py migrate --noinput
	python manage.py compilemessages
	python manage.py cleanuptokens
	python manage.py cleanupmedia
	python manage.py rqworker &
	python manage.py polltelegram &
	cron && tail -f /var/log/cron.log &
	exec python manage.py runserver 0.0.0.0:8000
fi

exec "$@"
