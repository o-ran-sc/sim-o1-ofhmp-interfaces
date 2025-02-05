# Performance Management

Performance management is a feature to report performance data.

## Overall architecture

Performance data is being generated using a predefined `template`.

Mode of operation:
- the data is being written into the `/ftp` folder (Docker-side only)
    - files are written at time intervals divisible by the `log-period`: for example, if the log period is 15 minutes, the files will be written at :00, :15, :30 and :45 respectively
    - filename is "A%Y%m%d.%H%M+0000-%H%M+0000_1_%hostname.xml where the time marks the start and end time
    - a VES FileReady message is being generated and sent
- the data is automatically deleted when it expires (`repetition-period`)


### performance-management/index.json

This file configures the performance data generation. It contains two objects:
- *config* used to configure the performance-management feature
- *values* which contain the values to be reported as data

`config` contains the following parameters:
- *log-period* - in seconds, is the period for writing a new file (using the values)
- *repetition-period* - in seconds, represents data validity; the data is usually deleted after this period
- *points* - a list of measurement point names (string)


`values` contains a list of objects, each object comprised of the points defined in the config
- the values are integer format
- each object *MUST* contain data for *ALL* points defined

### performance-management/template_5G_NR.xml

The template is defined by this file. By design, it is an XML file.

The **replace-variables** available inside are the following:
- `@start-time@` - represents the start time of the performance measurement
- `@end-time@` - represents the end time of the performance measurement
- `@suspect@` - is written only if the file does not contain a full log period
- `@log-period@` - log period as defined by the config, in interval representation (example: PT1S)
- `@rep-period@` - repetition period as defined by the config, in interval representation (example: PT2H30M)
- `@hostname@` - current device hostname
- `@point-start@` and `@point-end@` marks the definition of the points list
    - `@point-id@` - marks the point id
    - `@point-name@` - point name as defined in the config
- `@value-start@` and `@value-end@` marks the definition of the values list
    - `@point-id@` - marks the point id
    - `@value@` - value for the current point
