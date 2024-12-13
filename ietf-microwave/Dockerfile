FROM pynts-base:latest

COPY ./ietf-microwave/docker/yang /usr/local/share/yang/modules/pynts
COPY ./ietf-microwave/docker/scripts/install_yangs.sh /opt/dev/scripts/install_yangs.sh
COPY ./ietf-microwave/data /data

RUN \
    /opt/dev/scripts/install_yangs.sh

WORKDIR /app

ENV NETWORK_FUNCTION_TYPE="ietf-microwave"

EXPOSE 830
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
