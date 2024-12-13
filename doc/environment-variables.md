# PyNTS - Environment Variables

Below all the available environment variables will be described

## NETWORK_FUNCTION_TYPE
- should be automatically set by the Dockerfile to a specific network function that the image implements


## NETCONF_USERNAME
- type string

## NETCONF_PASSWORD
- type string

## SDNR_RESTCONF_URL
- type string
- URL for the RESTCONF interface of the SDN controller
- example: http://controller.dcn.smo.o-ran-sc.org

## SDNR_USERNAME
- type string
- SDNR credentials

## SDNR_PASSWORD
- type string
- SDNR credentials

## VES_URL
- type string
- URL of VES collector
- example: https://10.20.35.128:8443/eventListener/v7

## VES_USERNAME
- type string
- VES collector credentials

## VES_PASSWORD
- type string
- VES collector credentials

## NETWORK_INTERFACE
- type string
- the name of the network interface which can be used by the simulator. Is only relevant when docker image is ran in network_mode="host" (in this case, it needs to point to an interface name from the host system).

## O_DU_CALLHOME_PORT
- type string
- the port number where a simulated O-DU listens for call-home connections. Is only relevant when docker image is ran in network_mode="host". Default port is 4335