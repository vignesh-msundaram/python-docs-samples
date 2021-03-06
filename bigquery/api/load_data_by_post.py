#!/usr/bin/env python

# Copyright 2015, Google, Inc.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Command-line application that loads data into BigQuery via HTTP POST.

This sample is used on this page:

    https://cloud.google.com/bigquery/loading-data-post-request

For more information, see the README.md under /bigquery.
"""

import argparse
import json
import time

from googleapiclient import discovery
import httplib2
from oauth2client.client import GoogleCredentials


# [START make_post]
def make_post(http, schema, data, project_id, dataset_id, table_id):
    """
    Creates an http POST request for loading data into
    a bigquery table

    Args:
        http: an authorized httplib2 client,
        schema: a valid bigquery schema,
        see https://cloud.google.com/bigquery/docs/reference/v2/tables,
        data: valid JSON to insert into the table

    Returns: an http.request object
    """
    url = ('https://www.googleapis.com/upload/bigquery/v2/projects/' +
           project_id + '/jobs')
    # Create the body of the request, separated by a boundary of xxx
    resource = ('--xxx\n' +
                'Content-Type: application/json; charset=UTF-8\n' + '\n' +
                '{\n' +
                '   "configuration": {\n' +
                '     "load": {\n' +
                '       "schema": {\n'
                '         "fields": ' + str(schema) + '\n' +
                '      },\n' +
                '      "destinationTable": {\n' +
                '        "projectId": "' + project_id + '",\n' +
                '        "datasetId": "' + dataset_id + '",\n' +
                '        "tableId": "' + table_id + '"\n' +
                '      }\n' +
                '    }\n' +
                '  }\n' +
                '}\n' +
                '--xxx\n' +
                'Content-Type: application/octet-stream\n' +
                '\n')
    # Append data to the request body
    resource += data

    # Signify the end of the body
    resource += ('--xxx--\n')

    headers = {'Content-Type': 'multipart/related; boundary=xxx'}

    return http.request(url,
                        method='POST',
                        body=resource,
                        headers=headers)
    # [END make_post]


# [START poll_job]
def poll_job(bigquery, job):
    """Waits for a job to complete."""

    print('Waiting for job to finish...')

    request = bigquery.jobs().get(
        projectId=job['jobReference']['projectId'],
        jobId=job['jobReference']['jobId'])

    while True:
        result = request.execute(num_retries=2)

        if result['status']['state'] == 'DONE':
            if 'errorResult' in result['status']:
                raise RuntimeError(result['status']['errorResult'])
            print('Job complete.')
            return

        time.sleep(1)
# [END poll_job]


# [START main]
def main(project_id, dataset_id, table_name, schema_path, data_path):
    credentials = GoogleCredentials.get_application_default()
    http = credentials.authorize(httplib2.Http())
    bigquery = discovery.build('bigquery', 'v2', credentials=credentials)

    with open(schema_path, 'r') as schema_file:
        schema = schema_file.read()

    with open(data_path, 'r') as data_file:
        data = data_file.read()

    resp, content = make_post(
        http,
        schema,
        data,
        project_id,
        dataset_id,
        table_name)

    if resp.status == 200:
        job = json.loads(content)
        poll_job(bigquery, job)
        print("Success!")
    else:
        print("Http error code: {}".format(resp.status))
# [END main]

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('project_id', help='Your Google Cloud project ID.')
    parser.add_argument('dataset_id', help='A BigQuery dataset ID.')
    parser.add_argument(
        'table_name', help='Name of the table to load data into.')
    parser.add_argument(
        'schema_file',
        help='Path to a schema file describing the table schema.')
    parser.add_argument(
        'data_file',
        help='Path to the data file.')

    args = parser.parse_args()

    main(
        args.project_id,
        args.dataset_id,
        args.table_name,
        args.schema_file,
        args.data_file)
