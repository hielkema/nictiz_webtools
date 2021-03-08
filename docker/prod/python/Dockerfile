FROM python:3.9
MAINTAINER mertens@localhost

COPY ./app/requirements/ /opt/requirements/
#RUN pip install --no-cache-dir -r app/requirements/dev.txt
RUN pip install --no-cache-dir -r /opt/requirements/prod.txt

COPY ./ /webserver

WORKDIR /webserver

EXPOSE 8000


CMD ["gunicorn", "app.wsgi", "--timeout 90", "--workers 12", "--log-level=debug", "-b 0.0.0.0:8000"]