# PyNTS

PyNTS is a network topology simulator. Its focus is on the OpenFronthaul M-Plane and O1 management interfaces. It is written in Python as a modular application, which dynamically loads modules and extensions as it finds them available. The main code resides within the `application.py` file, and the methods here are responsible for instantiating and configuring logging, argument parsing and loading everything else.

## Core

The core of PyNTS handles instancing and starting of all the features and functionality.

The core module is the default loaded module by the application. It is the first to instantiate all the necessary modules and to start some features. The steps executed by the core module are as follows:
- instantiates any other base functionality of PyNTS (Config, REST, NETCONF)
- loading IetfSystemFeature
- loading NetconfAcmFeature
- loading CertificateExpirationNotifierFeature
- attempting to populate netconf data
- attempting VES pnfRegistration
- starting VES Heartbeat
- starting FaultManagement
- starting PerformanceManagement


### NETCONF Server

The NETCONF Server class handles the configuration of the NETCONF server (netopeer2-server).

<!-- ### REST API

REST API is used to control and check specific aspects of PyNTS, allowing the dynamic registration of REST endpoints.

The REST API endpoints are described by the extensions, modules and features which register such endpoints. -->

## Config

Configuring PyNTS is done through one or more of the following:
- environment variables (core)
- JSON configurations (for modules/features)
<!-- - REST API endpoints (for modules/features which support) -->

### Environment variables
You can find more information in the [Environment variables](environment-variables.md) page.

## Features

### Fault management
You can find more information in the [Fault Management](fault-management.md) page.

### Performance management
You can find more information in the [Performance Management](performance-management.md) page.

## Ports

- NETCONF SSH: depending on the configuration in ietf-netconf-server-running.json
- NETCONF TLS: depending on the configuration in ietf-netconf-server-running.json
- FTP: 21 (pmData /ftp)
- SFTP: 22 (pmData /ftp)

## Usage

For building the docker images to be used by the simulator, one can issue the command `make build-all` from the root of the repository.

This will result in building two docker images: one for the simulated O-RU (exposing OpenFronthaul M-Plane interface), and one for the simulated O-DU (exposing O1 interface).

The configuration of the NETCONF Server itself (whether it's SSH or TLS, whether it's normal connection or CallHome, the ports for listening etc.) is done through dynamically loading, at run-time, the configuration of the ietf-netconf-server model. There are some exmples for different cases.

### TLS NETCONF Configuration

Please note that `local-address` and `local-port` identify the local IP address and port where the NETCONF Server will listen for connections. 

A `local-address` can be set to `::` for listening on all IP addresses, including **IPv6**.

```json
{
  "ietf-netconf-server:netconf-server": {
    "listen": {
      "idle-timeout": 0,
      "endpoints": {
        "endpoint": [
          {
            "name": "tls-endpoint",
            "tls": {
              "tcp-server-parameters": {
                "local-address": "0.0.0.0",
                "local-port": 6513
              },
              "tls-server-parameters": {
                "server-identity": {
                  "certificate": {
                    "central-keystore-reference": {
                      "asymmetric-key": "serverkey-tls",
                      "certificate": "servercert-smo"
                    }
                  }
                },
                "client-authentication": {
                  "ca-certs": {
                    "central-truststore-reference": "cacerts"
                  }
                }
              },
              "netconf-server-parameters": {
                "client-identity-mappings": {
                  "cert-to-name": [
                    {
                      "id": 1,
                      "fingerprint": "02:DC:CB:E3:29:E2:65:04:A8:DF:B3:63:E7:E4:1A:06:81:64:C6:DA:37",
                      "map-type": "ietf-x509-cert-to-name:san-rfc822-name"
                    }
                  ]
                }
              }
            }
          }
        ]
      }
    }
  }
}
```

### SSH NETCONF Configuration

Please note that `local-address` and `local-port` identify the local IP address and port where the NETCONF Server will listen for connections. 

A `local-address` can be set to `::` for listening on all IP addresses, including **IPv6**.
```json
{
  "ietf-netconf-server:netconf-server": {
    "listen": {
      "endpoints": {
        "endpoint": [
          {
            "name": "ssh-endpoint-830",
            "ssh": {
              "tcp-server-parameters": {
                "local-address": "0.0.0.0",
                "local-port": 830
              },
              "ssh-server-parameters": {
                "server-identity": {
                  "host-key": [
                    {
                      "name": "melacon-key",
                      "public-key": {
                        "central-keystore-reference": "serverkey-ssh"
                      }
                    }
                  ]
                },
                "client-authentication": {
                  "users": {
                    "user": [
                      {
                        "name": "netconf",
                        "password": "$0$netconf!"
                      }
                    ]
                  }
                }
              }
            }
          }
        ]
      }
    }
  }
}
```

### NETCONF Call-Home via SSH

Please note that `remote-address` and `remote-port` identify the Call-Home endpoint (e.g. the SMO or the O-DU which listen for Call-Home connections).

```json
{
  "ietf-netconf-server:netconf-server": {
    "call-home": {
      "netconf-client": [
        {
          "name": "default-client",
          "endpoints": {
            "endpoint": [
              {
                "name": "default-ssh-callhome",
                "ssh": {
                  "tcp-client-parameters": {
                    "remote-address": "192.168.10.253",
                    "remote-port": 4334
                  },
                  "ssh-server-parameters": {
                    "server-identity": {
                      "host-key": [
                        {
                          "name": "melacon-key",
                          "public-key": {
                            "central-keystore-reference": "serverkey-ssh"
                          }
                        }
                      ]
                    },
                    "client-authentication": {
                      "users": {
                        "user": [
                          {
                            "name": "netconf",
                            "password": "$0$netconf!"
                          }
                        ]
                      }
                    }
                  }
                }
              }
            ]
          },
          "connection-type": {
            "persistent": {}
          }
        }
      ]
    }
  }
}
```

### NETCONF Call-Home via TLS

Please note that `remote-address` and `remote-port` identify the Call-Home endpoint (e.g. the SMO or the O-DU which listen for Call-Home connections).

```json
{
  "ietf-netconf-server:netconf-server": {
    "call-home": {
      "netconf-client": [
        {
          "name": "default-client",
          "endpoints": {
            "endpoint": [
              {
                "name": "tls-auth-endpt",
                "tls": {
                  "tcp-client-parameters": {
                    "remote-address": "172.60.0.71",
                    "remote-port": 4335
                  },
                  "tls-server-parameters": {
                    "server-identity": {
                      "certificate": {
                        "central-keystore-reference": {
                          "asymmetric-key": "serverkey-tls",
                          "certificate": "servercert"
                        }
                      }
                    },
                    "client-authentication": {
                      "ca-certs": {
                        "central-truststore-reference": "cacerts"
                      }
                    }
                  },
                  "netconf-server-parameters": {
                    "client-identity-mappings": {
                      "cert-to-name": [
                        {
                          "id": 1,
                          "fingerprint": "02:e9:38:1f:f6:8b:62:de:0a:0b:c5:03:81:a8:03:49:a0:00:7f:8b:f3",
                          "map-type": "ietf-x509-cert-to-name:specified",
                          "name": "netconf"
                        }
                      ]
                    }
                  }
                }
              }
            ]
          },
          "connection-type": {
            "persistent": {}
          }
        }
      ]
    }
  }
}
```

## Loading data

Data can be loaded in the NETCONF datastores at boot-time. By creating files having the name "[yang-module-name]-[datastore].[xml|json]", and placing them in /data folder (/data can be mounted in the docker container and all files present there will be considered for loading). The files can be in either `xml` or `json` format. The accepted datastores are `running` or `operational`.

## Starting the simulator

There are example docker-compose files for starting a simulated O-RU (actually 2 of them, one in hybrid mode, one in hierarchical mode) and another one for starting an O-DU. They can be started by simply doing `docker compose -f docker-compose-o-du-o1.yaml up -d` or `docker compose -f docker-compose-o-ru-mplane.yaml up -d`.
