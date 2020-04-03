FROM python:3.6-alpine3.10
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
WORKDIR /code
COPY requirements.txt /code/
RUN apk add --no-cache postgresql-libs postgresql-dev libxml2-dev libxslt-dev jpeg-dev zlib-dev bash apache2 apache2-dev apache2-ssl openssl && \
    apk add --no-cache --virtual .build-deps gcc musl-dev
ENV DOCKERIZE_VERSION v0.6.1
RUN wget https://github.com/jwilder/dockerize/releases/download/$DOCKERIZE_VERSION/dockerize-alpine-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && tar -C /usr/local/bin -xzvf dockerize-alpine-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && rm dockerize-alpine-linux-amd64-$DOCKERIZE_VERSION.tar.gz
RUN python3 -m pip install mod-wsgi==4.6.5
RUN python3 -m pip install numpy==1.16.2
RUN python3 -m pip install mkdocs==1.0.4
RUN python3 -m pip install --no-cache-dir -r requirements.txt
RUN apk --purge del .build-deps
RUN mod_wsgi-express module-config >> /etc/apache2/httpd.conf
COPY . /code/
COPY musicc.conf /etc/apache2/conf.d/
RUN rm -r /var/www/localhost/htdocs/*
ENV SSLEngine off
ENV SSLCertificateFile /code/dummy.crt
ENV SSLCertificateKeyFile /code/dummy.key
ENV SSLCertificateChainFile /code/dummy.crt
RUN echo "DUMMY FILE" >> /code/dummy.crt
RUN echo "DUMMY FILE" >> /code/dummy.key
RUN chmod +x /code/scripts/*.sh
RUN mkdocs build -t readthedocs --clean
ENV MUSICC_POSTGRES_HOST db
ENV MUSICC_POSTGRES_PORT 5432
ENTRYPOINT dockerize -wait tcp://$MUSICC_POSTGRES_HOST:$MUSICC_POSTGRES_PORT /code/scripts/deploy.sh