FROM python:3.6
MAINTAINER mertens@localhost

COPY ./app/requirements/ /opt/requirements/
#RUN pip install --no-cache-dir -r app/requirements/dev.txt
RUN pip install -r /opt/requirements/dev.txt

#COPY ./ /webserver

WORKDIR /webserver


COPY ./docker/dev/python/entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]