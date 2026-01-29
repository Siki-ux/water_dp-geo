#!/usr/bin/env sh

#############
# variables #
#############

MINIO_CERT_SOURCE="/tmp/bind/minio"
MINIO_CERT_TARGET="/tmp/volume/minio/certs"
MQTT_CERT_SOURCE="/tmp/bind/mqtt"
MQTT_CERT_TARGET="/tmp/volume/mqtt/certs"
CRONTAB="/tmp/volume/cron/crontab.txt"
FLYWAY_CONFIG="/tmp/conf/flyway"
MOSQUITTO_CONFIG="/tmp/conf/mosquitto"
NGINX_CONFIG="/tmp/conf/nginx"
KEYCLOAK_CONFIG="/tmp/conf/keycloak"

##################################
#  create volume subdirectories  #
##################################

mkdir -p $MINIO_CERT_TARGET
mkdir -p /tmp/volume/minio/vol0
mkdir -p $MQTT_CERT_TARGET
mkdir -p /tmp/volume/mqtt/auth
mkdir -p /tmp/volume/mqtt/data
mkdir -p /tmp/volume/cron
mkdir -p /tmp/volume/database/pgdata

####################
#  object-storage  #
####################

# 1. Copy SSH key from host if it exists
#    - If not, check if it exists in volume
#    - If not, generate a new SSH key
echo "Preparing SSH key for MinIO."
if [ -f "${MINIO_CERT_SOURCE}/id_ed25519" ]; then
    if ! cmp "${MINIO_CERT_SOURCE}/id_ed25519" "${MINIO_CERT_TARGET}/id_ed25519"; then
        echo "Copying SSH key from host."
        cp ${MINIO_CERT_SOURCE}/id_ed25519 ${MINIO_CERT_TARGET}/id_ed25519
    else
        echo "SSH key in volume is identical to host file. No action needed."
    fi
elif [ ! -f "${MINIO_CERT_TARGET}/id_ed25519" ]; then
    echo "No SSH key found in MinIO persistence volume, generating new SSH key."
    ssh-keygen -t ed25519 -f ${MINIO_CERT_TARGET}/id_ed25519 -N ""
else
    echo "SSH key already present in MinIO persistence volume."
fi

# 2. Check if FTP cert and key from host match those in volume
#    - If yes, skip copying/generation
#    - If not, check if they exist in volume and are valid
#    - If not, generate new self-signed certificates
echo "Preparing FTP certificate and key for MinIO."
# Check if source files exist and compare with target
if [ -f "${MINIO_CERT_SOURCE}/minio-ftp.crt" ] && [ -f "${MINIO_CERT_SOURCE}/minio-ftp.key" ] && \
   [ -f "${MINIO_CERT_TARGET}/minio-ftp.crt" ] && [ -f "${MINIO_CERT_TARGET}/minio-ftp.key" ]; then
    # Compare files using cmp (silent mode)
    if cmp "${MINIO_CERT_SOURCE}/minio-ftp.crt" "${MINIO_CERT_TARGET}/minio-ftp.crt" && \
       cmp "${MINIO_CERT_SOURCE}/minio-ftp.key" "${MINIO_CERT_TARGET}/minio-ftp.key"; then
        echo "FTP certificate and key in volume are identical to host files. No action needed."
    else
        echo "FTP certificate different in host and volume."
        echo "Copying FTP certificate and key from host to MinIO persistence volume."
        cp ${MINIO_CERT_SOURCE}/minio-ftp.crt ${MINIO_CERT_TARGET}/minio-ftp.crt
        cp ${MINIO_CERT_SOURCE}/minio-ftp.key ${MINIO_CERT_TARGET}/minio-ftp.key
    fi
elif [ -f "${MINIO_CERT_SOURCE}/minio-ftp.crt" ] && [ -f "${MINIO_CERT_SOURCE}/minio-ftp.key" ]; then
    echo "No FTP certificate and key in MinIO persistent volume."
    echo "Copying FTP certificate and key from host to MinIO persistence volume."
    cp ${MINIO_CERT_SOURCE}/minio-ftp.crt ${MINIO_CERT_TARGET}/minio-ftp.crt
    cp ${MINIO_CERT_SOURCE}/minio-ftp.key ${MINIO_CERT_TARGET}/minio-ftp.key
else
    if [ ! -f "${MINIO_CERT_TARGET}/minio-ftp.crt" ] || [ ! -f "${MINIO_CERT_TARGET}/minio-ftp.key" ] || \
       ! openssl x509 -checkend 604800 -noout -in ${MINIO_CERT_TARGET}/minio-ftp.crt; then
        echo "No valid certificate found in host or MinIO persistence volume."
        echo "Generating self-signed certificate and key."
        openssl req -new -newkey rsa:2048 -days 90 -nodes -x509 \
            -keyout ${MINIO_CERT_TARGET}/minio-ftp.key \
            -out ${MINIO_CERT_TARGET}/minio-ftp.crt \
            -subj "/C=DE/O=Helmholtz-Zentrum für Umweltforschung GmbH - UFZ/OU=RDM/CN=ZID TSM Development CA" \
            -addext "subjectAltName = DNS:localhost" \
            -addext "basicConstraints=critical,CA:FALSE"
        echo "New self-signed certificate and key generated in MinIO persistence volume."
    fi
fi

#################
#  mqtt-broker  #
#################

# 1. Always copy ca.crt, server.cert and server.key from host if they exist
#    - If not, check if cert exist in volume and are valid
#    - If not, generate new self-signed certificates

# needs a bit of cleanup

echo "Preparing TLS certificate and key for Mosquitto."

if [ -f "${MQTT_CERT_SOURCE}/server.crt" ] && [ -f "${MQTT_CERT_SOURCE}/server.key" ] && [ -f "${MQTT_CERT_SOURCE}/ca.crt" ]; then
    if [ -f "${MQTT_CERT_TARGET}/server.crt" ] && [ -f "${MQTT_CERT_TARGET}/server.key" ] && [ -f "${MQTT_CERT_TARGET}/ca.crt" ]; then
        if cmp -s "${MQTT_CERT_SOURCE}/server.crt" "${MQTT_CERT_TARGET}/server.crt" && \
        cmp -s "${MQTT_CERT_SOURCE}/server.key" "${MQTT_CERT_TARGET}/server.key" && \
        cmp -s "${MQTT_CERT_SOURCE}/ca.crt" "${MQTT_CERT_TARGET}/ca.crt"; then
            echo "TLS certificates and key in volume are identical to host files. No action needed."
        else
            echo "TLS certificate and key different in host and volume."
            echo "Copying TLS certificates and key from host to MQTT persistence volume."
            cp ${MQTT_CERT_SOURCE}/server.crt ${MQTT_CERT_TARGET}/server.crt
            cp ${MQTT_CERT_SOURCE}/server.key ${MQTT_CERT_TARGET}/server.key
            cp ${MQTT_CERT_SOURCE}/ca.crt ${MQTT_CERT_TARGET}/ca.crt
        fi
    fi
elif [ -f "${MQTT_CERT_SOURCE}/server.crt" ] && [ -f "${MQTT_CERT_SOURCE}/server.key" ] && [ -f "${MQTT_CERT_SOURCE}/ca.crt" ]; then
    echo "No TLS certificate and key yet in persistence volume."
    echo "Copying TLS certificates and key from host to MQTT persistence volume."
    cp ${MQTT_CERT_SOURCE}/server.crt ${MQTT_CERT_TARGET}/server.crt
    cp ${MQTT_CERT_SOURCE}/server.key ${MQTT_CERT_TARGET}/server.key
    cp ${MQTT_CERT_SOURCE}/ca.crt ${MQTT_CERT_TARGET}/ca.crt
else
    if [ ! -f "${MQTT_CERT_TARGET}/server.crt" ] || [ ! -f "${MQTT_CERT_TARGET}/server.key" ] || [ ! -f "${MQTT_CERT_TARGET}/ca.crt" ] || \
    ! openssl x509 -checkend 604800 -noout -in ${MQTT_CERT_TARGET}/server.crt ; then
        echo "No valid certificates found in MQTT persistence volume."
        echo "Generating new self-signed ca.crt ..."
        openssl req -new -newkey rsa:2048 -days 90 -nodes -x509 \
            -keyout ${MQTT_CERT_TARGET}/ca.key \
            -out ${MQTT_CERT_TARGET}/ca.crt \
            -subj "/C=DE/O=Helmholtz-Zentrum für Umweltforschung GmbH - UFZ/OU=RDM/CN=time.IO Development CA" \
            -addext "basicConstraints=critical,CA:TRUE"
        echo "Generate server.key and server.csr ..."
        openssl req -new -newkey rsa:2048 -nodes \
            -keyout ${MQTT_CERT_TARGET}/server.key \
            -out ${MQTT_CERT_TARGET}/server.csr \
            -subj "/C=DE/O=Helmholtz-Zentrum für Umweltforschung GmbH - UFZ/OU=RDM/CN=time.IO Development CA" \
            -addext "subjectAltName = DNS:localhost" \
            -addext "basicConstraints=critical,CA:FALSE"
        echo "Sign server.csr with CA to get server.crt ..."
        openssl x509 -req -days 90 -in ${MQTT_CERT_TARGET}/server.csr \
            -CA ${MQTT_CERT_TARGET}/ca.crt -CAkey ${MQTT_CERT_TARGET}/ca.key -CAcreateserial \
            -out ${MQTT_CERT_TARGET}/server.crt
        echo "New self-signed certificates generated in MQTT persistence volume."
    fi
fi

# Create crontab.txt if it not already exists
if [ ! -f $CRONTAB ]; then
    touch $CRONTAB
    chmod 666 $CRONTAB
    echo "# * * * * * /place-sms-and-other-manual-commands-here.sh" >> $CRONTAB
fi

###########################################
#  set volume ownerships and permissions  #
###########################################

# only run if USE_CHOWN is set to "true"
if [ "${USE_CHOWN}" == "true" ]; then
    echo "Setting ownership of volume directories (except minio) to ${SYSTEM_USER}:${SYSTEM_USER}."
    chown -R ${SYSTEM_USER}:${SYSTEM_USER} \
        /tmp/volume/mqtt \
        /tmp/volume/cron \
        /tmp/volume/database \
        /tmp/volume/visualization \
        /tmp/volume/tomcat
else
    echo "Skipping chown of volume directories as USE_CHOWN is not set to 'true'."
fi

if [ "${USE_CHOWN_OBJECT_STORAGE}" == "true" ]; then
    echo "Setting ownership of minio volume directory to ${OBJECT_STORAGE_USER}:${OBJECT_STORAGE_USER}."
    chown -R ${OBJECT_STORAGE_USER}:${OBJECT_STORAGE_USER} \
        /tmp/volume/minio
else
    echo "Skipping chown of volume directories as USE_CHOWN is not set to 'true'."
fi

#chmod -R u+rwX,g+rwX \
#      /tmp/volume/minio \
#      /tmp/volume/mqtt \
#      /tmp/volume/cron \
#      /tmp/volume/database \
#      /tmp/volume/visualization \
#      /tmp/volume/tomcat


###########################################
#  set local file permissions for others  #
#  inherit from group, except read        #
###########################################

chmod -R o=g-w $FLYWAY_CONFIG $MOSQUITTO_CONFIG $NGINX_CONFIG $KEYCLOAK_CONFIG
echo "Updated permissions for flyway, mosquitto, nginx and keycloak config files."
