activity-chart
==============

Tool to generate a graph of commits per day.

The tool reads the repository information of one or more Mercurial repositories
and builds a chart with commit activity per day. This is similar to the commit
chart in github, but generated locally. It creates an SVG file, and launches a
file viewer to display it.

Notice that the mercurial module is not supported in Python3, so we have to use
Python 2.7
