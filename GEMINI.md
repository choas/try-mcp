# MVG MCP

## Setup and Start

This are the first steps:

- create an MCP service to find routes in Munich, Germany
- use Python, therefore install all necessary packages and setup a venv
- write a Python program and use "mvg" library; don't use other "mvg" APIs, because they might be outdated
- the MCP service takes a start and end destination, time (if not set use now) and a arrival time, if the time isn't the depart time

## Next steps

In a next step:

- implement the routing in a way that different connections can be taken, if there is no direct connection

## Current Status

- The MCP service is implemented in `main.py`.
- It takes a start and end destination as command-line arguments.
- It also accepts optional `--time` and `--arrival` flags.
- The service currently only attempts to find direct connections.
- **Limitation:** The `mvg` library does not provide an easy way to get the stops for a given line without a paid API key. This makes it difficult to accurately determine if a route is a direct connection. The current implementation has a temporary workaround, but it is not reliable.

## mvg library is the way to go

As [https://pypi.org/project/mvg/] describes why mvg library was implemented

> The package PyMVGLive from 2017 does provide an interface to the former MVGLive API at mvg-live.de. As of 2022 the MVGLive website does not exist anymore and the package has been archived. Although the old API still works for some stations, it does not for others - mainly due to updated station identifiers. Therefore, the package is considered deprecated and cannot be used for new designs.
> The newer package mvg-api offers an implementation from 2020 based on the API at www.mvg.de/api/fahrinfo, which went offline in 2024. It considered the updated station identifiers and provided the basis for other projects such as mvg-cli.