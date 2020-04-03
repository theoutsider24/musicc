## Docker

The MUSICC docker image includes:

* Alpine Linux 3.10  
* Python 3.6
* Apache 2.4
* Django 2.2
* mod-wsgi 4.6.5

The image contains a basic Apache configuration including support for enabling ssl

**NOTE Apache-served static elements currently bypass Django's authentication allowing for un-authenticated users to access them**

**This includes images, resources, documentation and other static content**

**This will be addressed in future releases**


<h3>Environment variables</h3>
**NOTE Default passwords should be changed in production**

| Variable                       |           Example values            | Default                             |                                                                                                                                                                      Description |
| :----------------------------- | :---------------------------------: | ----------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------: |
| MUSICC_MASTER_HOST             | 'https://musicc.ts-catapult.org.uk' | 'https://musicc.ts-catapult.org.uk' |                                                                                                The musicc system to use as the master system for the purposes of synchronisation |
| MUSICC_ADMIN_REQUIRES_APPROVAL |            True or False            | False                               |                                                                                            Whether MUSICC admins should be allowed to perform actions without requiring approval |
| MUSICC_DEBUG_MODE              |            True or False            | False                               |                                                                                                                                             Enables/Disables Django's debug mode |
| MUSICC_POSTGRES_HOST           |        'my_postgres_server'         | 'localhost'                         |                                                                                                      See [Django HOST](https://docs.djangoproject.com/en/2.2/ref/settings/#host) |
| MUSICC_POSTGRES_PORT           |                5432                 | 5432                                |                                                                                                      See [Django PORT](https://docs.djangoproject.com/en/2.2/ref/settings/#port) |
| MUSICC_POSTGRES_NAME           |            'my_db_name'             | 'postgres'                          |                                                                                                      See [Django NAME](https://docs.djangoproject.com/en/2.2/ref/settings/#name) |
| MUSICC_POSTGRES_USER           |         'my_postgres_user'          | 'postgres'                          |                                                                                                      See [Django USER](https://docs.djangoproject.com/en/2.2/ref/settings/#user) |
| MUSICC_POSTGRES_PASSWORD       |            'myPa55w0rd'             | 'postgres'                          |                                                                                              See [Django PASSWORD](https://docs.djangoproject.com/en/2.2/ref/settings/#password) |
| SSLEngine                      |            'on' or 'off'            | 'off'                               |                                                                                         see [Apache SSLEngine](https://httpd.apache.org/docs/current/mod/mod_ssl.html#sslengine) |
| SSLCertificateFile             |      '/path/to/cert/file.cer'       | ''                                  |       see [Apache SSLCertificateFile](https://httpd.apache.org/docs/current/mod/mod_ssl.html#sslcertificatefile) Certificate directory must be implemented using shared volumes. |
| SSLCertificateKeyFile          |      '/path/to/cert/file.key'       | ''                                  | see [Apache SSLCertificateKeyFile](https://httpd.apache.org/docs/current/mod/mod_ssl.html#SSLCertificateKeyFile) Certificate directory must be implemented using shared volumes. |
| MUSICC_DEFAULT_FROM_EMAIL      |       'an.email@address.com'        | 'webmaster@localhost'               |                                                                          see [Django DEFAULT_FROM_EMAIL](https://docs.djangoproject.com/en/2.2/ref/settings/#default-from-email) |
| MUSICC_EMAIL_USE_TLS           |            True or False            | False                               |                                                                                          See [Django USE_TLS](https://docs.djangoproject.com/en/2.2/ref/settings/#email-use-tls) |
| MUSICC_EMAIL_HOST              |           'smtp.host.com'           | 'locahost'                          |                                                                                          See [Django EMAIL_HOST](https://docs.djangoproject.com/en/2.2/ref/settings/#email-host) |
| MUSICC_EMAIL_PORT              |                 587                 | 25                                  |                                                                                          See [Django EMAIL_PORT](https://docs.djangoproject.com/en/2.2/ref/settings/#email-port) |
| MUSICC_EMAIL_HOST_USER         |        'my.user@address.com'        | ''                                  |                                                                                See [Django EMAIL_HOST_USER](https://docs.djangoproject.com/en/2.2/ref/settings/#email-host-user) |
| MUSICC_EMAIL_HOST_PASSWORD     |            'myPa55w0rd'             | ''                                  |                                                                        See [Django EMAIL_HOST_PASSWORD](https://docs.djangoproject.com/en/2.2/ref/settings/#email-host-password) |

---


## Docker compose
Docker compose allows the deployment of multi-container configurations

<h3>Sample configurations</h3>

<h4>Basic configuration</h4>

```yml
version: '3'

services:
  db:
    image: postgres:12
    networks:
      - deploy_net
  web:
    image: connectedplacescatapult/musicc
    ports:
      - "80:80"
    networks:
      - deploy_net
    depends_on:
      - db
networks:
  deploy_net:
```

<h4>Full production configuration</h4>
Note that postgres settings remain unaltered because a default postgres container is being used - This means that the default host, port and credentials will be used

```yml
version: '3'

services:
  db:
    image: postgres:12
    networks:
      - deploy_net
  web:
    image: connectedplacescatapult/musicc
    ports:
      - "80:80"
      - "443:443"
    networks:
      - deploy_net
    environment:
      - SSLEngine='on'
      - SSLCertificateFile='/certs/certificate.crt'
      - SSLCertificateKeyFile='/certs/privatekey.key'
      - MUSICC_DEBUG_MODE=False
      - MUSICC_ADMIN_REQUIRES_APPROVAL=True
      - MUSICC_DEFAULT_FROM_EMAIL='my.email@address.com'
      - MUSICC_EMAIL_USE_TLS=True
      - MUSICC_EMAIL_HOST='smtp.gmail.com'
      - MUSICC_EMAIL_PORT=587
      - MUSICC_EMAIL_HOST_USER='my.email@address.com'
      - MUSICC_EMAIL_HOST_PASSWORD='myPa55w0rd'
    user: root
    restart: unless-stopped
    volumes:
      - "/dir/containing/my/certs:/certs"
      - "./logs:/code/logs"
      - "./logs/apache:/var/www/logs"
    depends_on:
      - db
networks:
  deploy_net:
```


---