FROM python:3.4

ADD ./messengerext /app/messengerext
ADD ./requirements_* ./docker-entrypoint.sh /app/
ADD docker/crontab /etc/cron.d/groupsome-cron
WORKDIR /app

RUN pip install --no-cache-dir -r requirements_production.txt

RUN echo "deb http://www.deb-multimedia.org jessie main non-free" >> /etc/apt/sources.list
RUN gpg --keyserver pgpkeys.mit.edu --recv-key 5C808C2B65558117 && gpg -a --export 5C808C2B65558117 | apt-key add -

RUN apt-get update && apt-get install -y \
		ca-certificates \
		wget \
		gcc \
		gettext \
		mysql-client libmysqlclient-dev \
		postgresql-client libpq-dev \
		sqlite3 \
		libtiff5-dev libjpeg62-turbo-dev zlib1g-dev \
    libfreetype6-dev liblcms2-dev libwebp-dev tcl8.6-dev tk8.6-dev python-tk webp \
    ffmpeg \
    cron \
	--no-install-recommends && rm -rf /var/lib/apt/lists/*

RUN set -ex \
	&& wget -q https://nodejs.org/dist/v6.5.0/node-v6.5.0-linux-x64.tar.xz \
	&& tar -xvf node-v6.5.0-linux-x64.tar.xz \
	&& cp -R node-v6.5.0-linux-x64/bin/ node-v6.5.0-linux-x64/include/ node-v6.5.0-linux-x64/lib/ node-v6.5.0-linux-x64/share/ /usr/local \
	&& rm -r node-v6.5.0-linux-x64 \
	&& rm node-v6.5.0-linux-x64.tar.xz \
	&& npm install -g stylus yuglify

RUN set -ex \
	&& mkdir /uploaded-media \
	&& chmod 0644 /etc/cron.d/groupsome-cron \
	&& touch /var/log/cron.log \
	&& crontab /etc/cron.d/groupsome-cron

EXPOSE 8000
VOLUME ["/app", "/uploaded-media"]
ENV DJANGO_SETTINGS_MODULE="config.settings_docker"

ENTRYPOINT ["sh", "/app/docker-entrypoint.sh", "runserver"]
