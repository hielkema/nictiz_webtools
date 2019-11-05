FROM nginx:latest
# Tested successfully on 1.17

RUN rm /etc/nginx/conf.d/default.conf

COPY ./docker/prod/nginx/django.conf /etc/nginx/conf.d/