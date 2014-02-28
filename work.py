#!/usr/bin/python2.7

"""Tool to generate a graph of commits per day.

The tool reads the repository information of one or more Mercurial repositories
and builds a chart with commit activity per day. This is similar to the commit
chart in github, but generated locally. It creates an SVG file, and launches a
file viewer to display it.

Notice that the mercurial module is not supported in Python3, so we have to use
Python 2.7
"""

__author__ = 'jt@javiertordable.com (Javier Tordable)'

from mercurial import hg, changelog, ui
from svgwrite import Drawing

import argparse
from datetime import date, timedelta
import math
import subprocess
import sys
import os

# Chart file configuration.
CHART_FILE_NAME = 'work.svg'
CHART_FILE_PATH = os.getcwd()
CHART_VIEWER = 'eog'

# Visualization style.
NUM_DAYS_TO_SHOW = 365
DAY_BOX_SIZE = 11
DAY_BOX_SEPARATION = 2
DISTANCE_BETWEEN_BOXES = DAY_BOX_SIZE + DAY_BOX_SEPARATION
MARGIN = 6

# Box colors, sorted from weaker to stronger.
BOX_COLORS = ['#eeeeee', '#d6e685', '#8cc665', '#44a340', '#1e6823']

def create_empty_chart(full_file_name):
    """Creates a chart of the proper dimensions with a white background."""
    num_days_in_week = 7
    num_weeks = math.ceil(NUM_DAYS_TO_SHOW / 7.0)
    if date.today().weekday() + 1 < NUM_DAYS_TO_SHOW % 7:
        # We need to draw NUM_DAYS_TO_SHOW % 7 extra days, but on the last week
        # we have only space for date.today().weekday() + 1 days.
        num_weeks += 1

    width = 2 * MARGIN + num_weeks * DAY_BOX_SIZE + \
        (num_weeks - 1) * DAY_BOX_SEPARATION
    height = 2 * MARGIN + num_days_in_week * DAY_BOX_SIZE + \
        (num_days_in_week - 1) * DAY_BOX_SEPARATION

    chart = Drawing(full_file_name, size=(width, height))
    chart.add(chart.rect(insert=(0, 0), size=(width, height), fill='white'))
    return chart

def get_box_color(count):
    """Returns the box color that corresponds to the given count."""
    if count < 1:
        return BOX_COLORS[0]
    elif count == 1:
        return BOX_COLORS[1]
    elif 2 <= count <= 3:
        return BOX_COLORS[2]
    elif 4 <= count <= 5:
        return BOX_COLORS[3]
    else:  # 6 <= count.
        return BOX_COLORS[4]

def draw_daily_boxes(chart, start_date, cl_counts):
    """Draws the boxes for CL counts for each day."""
    first_day_to_show = start_date.weekday()
    last_day_to_show = first_day_to_show + NUM_DAYS_TO_SHOW
    for day_index in range(first_day_to_show, last_day_to_show):
        # Boxes are stacked first by column and then by row.
        x = MARGIN + (day_index // 7) * DISTANCE_BETWEEN_BOXES
        y = MARGIN + (day_index % 7) * DISTANCE_BETWEEN_BOXES

        # Compute the real date from the day index.
        day = start_date + timedelta(days=(day_index - first_day_to_show))
        if day in cl_counts:
            color = get_box_color(cl_counts[day])
        else:
            color = get_box_color(0)

        chart.add(chart.rect(insert=(x,y),
                             size=(DAY_BOX_SIZE, DAY_BOX_SIZE),
                             fill=color))

def extract_cl_counts(repository_path, cl_counts):
    """Reads the repository changelog and extracts CL counts per day."""
    repository = hg.repository(ui.ui(), repository_path)
    changelog = repository.changelog
    for cl_index in changelog:
        cl_id = changelog.lookup(cl_index)
        cl = changelog.read(cl_id)

        # The timestamp seems to be the 3rd field in the CL.
        # It's given in a tuple. The UNIX timestap is the first field.
        timestamp = cl[2][0]
        cl_date = date.fromtimestamp(timestamp)

        if cl_date in cl_counts:
            cl_counts[cl_date] = cl_counts[cl_date] + 1
        else:
            cl_counts[cl_date] = 1

def view_chart(full_file_name):
    """Launch the image viewer to open the SVG file."""
    # Don't print initialization errors.
    subprocess.call([CHART_VIEWER, full_file_name], stderr=open(os.devnull))

def main():
    parser = argparse.ArgumentParser(description=sys.modules[__name__].__doc__)
    parser.add_argument('path', nargs='*', default=None,
                        help='Root directory for the Mercurial repository.')
    args = parser.parse_args()

    # Get the changelog data from each repository.
    cl_counts = {}
    if args.path:
        for repository_path in args.path:
            extract_cl_counts(repository_path, cl_counts)
    else:
        # Assume that the current path has a repository.
        extract_cl_counts(os.getcwd(), cl_counts)

    # Draw the chart and save it in a file.
    full_file_name = os.path.join(CHART_FILE_PATH, CHART_FILE_NAME)
    chart = create_empty_chart(full_file_name)
    start_date = date.today() - timedelta(days=(NUM_DAYS_TO_SHOW - 1))
    draw_daily_boxes(chart, start_date, cl_counts)
    chart.save()

    # Open the image file and print total count.
    view_chart(full_file_name)
    print('Changes as of: ' + str(date.today()) + ': ' + \
              str(sum(cl_counts.itervalues())))

if __name__ == '__main__':
    main()
