# Get started with ZID/TSM

The orchestration repository is the place where all the little [ZID/TSM
components](https://git.ufz.de/rdm-software/timeseries-management) are
combined to a running system. This is achieved by putting the docker
images of the ZID/TSM components together in a
[docker compose file](docker-compose.yml) so you can start them with a
single command and without deeper knowledge of every single part of it.

Used [ZID/TSM
components](https://git.ufz.de/rdm-software/timeseries-management) in
that repo:

- [tsm-orchestration](https://git.ufz.de/rdm-software/timeseries-management/tsm-orchestration)
- [tsm-extractor](https://git.ufz.de/rdm-software/timeseries-management/tsm-extractor)
- [tsm-dispatcher](https://git.ufz.de/rdm-software/timeseries-management/tsm-dispatcher)
- [TSM Basic Demo Scheduler](https://git.ufz.de/rdm-software/timeseries-management/tsm-basic-demo-scheduler)

## 1. Create environment/config file from example:

```bash
cp .env.example .env 
```
The settings from the example are ok for local testing and development.
Postgres, Minio and MQTT services are exposed on localhost, so you can
access them with clients from your machine.

When using this in (semi-) production (e.g. on a server) some settings,
especially the passwords should be changed! Also keep in mind, that you
will need encryption when exposing the services: For example, minio HTTP
ports will need a TLS proxy (i.e. nginx) with certificates (i.e.
issued by
[DFN PKI](https://www.pki.dfn.de/geant-trusted-certificate-services/)).

##  2. Run all the services and have fun

- To start the services:
  - execute `./up.sh`
- To stop the services:
  - execute `./down.sh`
- To start the services including the `docker-compose-dev.yml` (see chapter "Extend or override docker-compose" for more information)
  - execute `./up-with-dev.sh` 
- To stop the services including the `docker-compose-dev.yml`
  - execute `./down-with-dev.sh`
- To execute any docker compose command use either
  -  `./dc.sh` <command>
  -  `./dc-with-dev.sh` <command>

It will take some seconds until everything is up.

## 3. Create a thing

A *thing* in ZID/TSM/STA sense is an entity that is producing time
series data in one or more data streams. In ZID/TSM we follow the
approach, that an end user is able to create a new *thing* and all its
settings for its infrastructure like database credentials or parser
properties. When somebody enters or changes settings of a *thing* these
changes are populated to *action services* by MQTT events.

As long as ZID/TSM doesn't have a graphical end user frontend we have to
produce events by ourselves. We directly use the MQTT container for
that:

```bash
cat thing-event-msg.json | docker-compose exec -T mqtt-broker sh -c "mosquitto_pub -t thing_creation -u \$MQTT_USER -P \$MQTT_PASSWORD -s"
```

The dispatcher action services will create
- a new minio user and bucket:
  - <http://localhost:9001/buckets/thedoors-057d8bba-40b3-11ec-a337-125e5a40a849/admin/summary>
  - <http://localhost:9001/buckets/thedoors-057d8bba-40b3-11ec-a337-125e5a40a849/browse>
- a new postgres database role and schema:
  - <postgresql://myfirstproject_6185a5b8462711ec910a125e5a40a845:d0ZZ9d3QSDZ6tXIZTnKRY1uVLKIc05GmQh8SA36M@postgres/postgres>
  -   and a *thing* entity with (hopefully) all the necessary properties
      in the new `thing` table

## 4. Upload data

Now you can go to the fresh new bucket in the
[minio console](http://localhost:9001/buckets/thedoors-057d8bba-40b3-11ec-a337-125e5a40a849/browse)
and upload a `csv` file.

The dispatcher action service called *run-process-new-file-service* gets
notified by a MQTT event produced by minio and will forward the file
resource and the necessary settings to the scheduler. The scheduler
starts the extractor wo will parse the data and write it to the things
database.

## 5. Clean up

To temporary stop the containers and services use `docker-compose stop`.

When you're ready or destroyed your setup while playing around you can
reset everything by kicking away the containers and removing all data:

```bash
docker-compose down --timeout 0 -v --remove-orphans && ./remove-all-data.sh
```

All data is lost with this. Be careful!

# Using SFTP and FTP for uploads 

The minio object storage provides SFTP and FTP services. Its automatically equipped with self signed TLS certs for FTP
and a generated SSH host key. Please change the TLs certificates to some officially signed, you can take the same certs
that are used by the proxy.

You can directly use the minio accounts, but it would be better to use minio service accounts for authentication.

## Testing FTP service with `lftp`

With the [previously generated account](#3-create-a-thing) and the default settings:

```bash
lftp -p 40021 thedoors-057d8bba-40b3-11ec-a337-125e5a40a849@localhost -e "set ssl:ca-file ./data/minio/certs/minio-ftp.crt"
```

In development mode with self signed certificate we have to define the CA. 

## Testing SFTP service with `sftp`

With the [previously generated account](#3-create-a-thing) and the default settings:

```bash
sftp -P 40022 thedoors-057d8bba-40b3-11ec-a337-125e5a40a849@localhost
```

# Further thoughts and hints

## Configuring and operating Mosquitto MQTT broker

## General

When using in production it is recommended to use the `mosquitto.tls.conf` template (change
`MOSQUITTO_CONFIG` in your `.env` file) to enable encrypted connections by tls.

When started the first time it generates a password database
(`data/mosquitto/passwd/mosquitto.passwd`) with the credentials from the environment. Later 
changes of the password and user in env do not have any effect to the password file but will
break the health check of the service. To change passwords or add users use the 
`mosquitto_passwd` command from inside the container:

```bash
docker-compose run --rm mqtt-broker mosquitto_passwd -b /tmp/mosquitto/auth/mosquitto.passwd "user" "password"
```

With interactive password input:

```bash
docker-compose run --rm mqtt-broker mosquitto_passwd /tmp/mosquitto/auth/mosquitto.passwd "user"
```

### Example for adding a new user and an acl to publish data

1. Start the mqtt-broker service with `docker-compose up mqtt-broker` at least once the create 
   the initial `mosquitto.passwd` and `mosquitto.acl` files.
2. Call ``docker-compose exec mqtt-broker bash -c $'echo `echo -n "MY_NEW_MQTT_USER:" && /mosquitto/pw -p "MY_NEW_MQTT_PASSWORD"` >> /tmp/mosquitto/auth/mosquitto.passwd'``
   to add the new user with its password 
3. Restart the mqtt-broker service `docker-compose restart mqtt-broker`
4. From now on you should be able to publish to the new users topic namespace:
   ```bash
   echo "very nice data!" | docker-compose exec -T mqtt-broker sh -c "mosquitto_pub -t mqtt_ingest/MY_NEW_MQTT_USER/beautiful/sensor/1 -u MY_NEW_MQTT_USER -P MY_NEW_MQTT_PASSWORD -s"
   ```
   Watch them by checking the output of the mqtt-cat service:
   `docker-compose logs --follow mqtt-cat`

### mosquitto_ctrl

[mosquitto_ctrl](https://mosquitto.org/man/mosquitto_ctrl-1.html) seems to be a new API to 
configure the mosquitto server on runtime without to reload it when things change.

### Mosquitto auth plugins

For dynamic acls from database: https://gist.github.com/TheAshwanik/7ed2a3032ca16841bcaa


## Minio

- Yes, we really need four volumes, otherwise object lock will not work.
- Find the current event ARN to configure bucket notifications:

    ```bash
    mc admin info  myminio/ --json | jq .info.sqsARN
    ```

## Naming conventions

Human readable ID for projects and things: Use UUID as suffix and
sanitized name to fill it from the left until it is 63 chars long.

```pathon
import re


def slug(self):
    return re.sub(
        '[^a-z0-9_]+',
        '',
        '{shortname}_{uuid}'.format(shortname=self.name[0:30].lower(), uuid=self.uuid)
    )
    
# Or with minus chars at all but less space for the name
    def slug_with_minus(self):
        return re.sub(
            '[^a-z0-9\-]+',
            '',
            '{shortname}-{uuid}'.format(shortname=self.name[0:26].lower(), uuid=self.uuid)
        )
```

# Enable TLS Security for Postgres database

For secure connections over the network you need transport security like
`https`. To achieve this you need certificates of a public key
infrastructure (PKI) like the
[DFN PKI](https://www.pki.dfn.de/geant-trusted-certificate-services/).

Once you have a private key and a public certificate you can enable
security by

- changing `POSTGRES_TLS_CERT_PATH` to the path of your certificate file
- changing `POSTGRES_TLS_KEY_PATH` to the path of your private key file
- uncommenting the line beginning with `POSTGRES_EXTRA_PARAMS`

in the `.env` file of your deployment.

Now you're able to access the minio service with `https`. The postgres
database will enforce encryption but you need to enable
[`full-verification`](https://stackoverflow.com/questions/14021998/using-psql-to-connect-to-postgresql-in-ssl-mode) mode in client to also check the identity of the
server.

# Extend or override docker-compose

- preparations:
  - copy `docker-compose-dev.example.yml` and rename it to `docker-compose-dev.yml`
  - add your changes to `docker-compose-dev.yml`
  - note: changes to `docker-compose-dev.yml` are not added to version control
- To run locally and override or extend the `docker-compose.yml` you can use the following command:  
  -  `docker compose -f docker-compose.yml -f docker-compose-dev.yml  up -d`

## Mount local repositories into services

If you use the workflow described above (without making changes to `docker-compose-dev.example.env`), it will mount the code of the other local TSM repositories into their respective services. If you now make changes to the code or check out another branch in a repository, it will directly be present inside the services defined in the `docker-compose-dev.example.yml`. This way you don't have to build an image every time you change something in the code.

Please note that this will only work if you have the other TSM respositories in the same parent directory as tsm-orchestration, as shown below.

``` 
TSM_DIRECTORY (can be any dir)
├── tsm-orchestration
├── tsm-dispatcher
├── tsm-frontend
├── tsm-basic-demo-scheduler
├── tsm-extractor
└── tsm-ufz-tsmdl
```

# Keycloak as identity provider in development environment

## Admin console

- http://localhost:8081/admin/master/console/#/demo/ 
  - or: http://keycloak:8081/admin/master/console/#/demo/ (if you updated /etc/hosts)
  - or: http://keycloak:KEYCLOAK_PORT/admin/master/console/#/demo/ || http://localhost:KEYCLOAK_PORT/admin/master/console/#/demo/ (if you changed the port to something other than 8081) 
- Credentials:
  - User: `admin`
  - Password: `admin`

See [here](./keycloak/README.md) for further information regarding configuration and setup.