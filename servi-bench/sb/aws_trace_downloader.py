import logging
import json
import boto3
from botocore.config import Config


class AwsTraceDownloader:
    """Implements get_traces(self) to download X-Ray traces using the AWS Python library boto3:
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/xray.html
    More documentation on getting data from X-Ray including example trace:
    https://docs.aws.amazon.com/xray/latest/devguide/xray-api-gettingdata.html
    """

    def __init__(self, spec) -> None:
        self.spec = spec
        # Configure AWS XRay client
        region = self.spec['region']
        my_config = Config(
            region_name=region
        )
        self.client = boto3.client('xray', config=my_config)

    def get_traces(self):
        """Retrieves X-Ray traces from the last invocation:
        1. saves all trace ids in a trace_ids.txt
        2. saves all actual trace data in traces.json
        3. saves unprocessed trace ids in unprocessed_trace_ids.txt
        """
        start, end = self.spec.event_log.get_invoke_timespan()
        log_path = self.spec.logs_directory()
        trace_ids_file = log_path.joinpath('trace_ids.txt')
        trace_file = log_path.joinpath('traces.json')
        if trace_file.exists():
            logging.error(f"Traces already exist under {trace_file} for this \
invocation starting time. Aborting.")
            return None

        trace_ids = self.retrieve_trace_ids(start, end, trace_ids_file)

        # Remove potential duplicates because boto3 BatchGetTraces fails if
        # a chunk contains duplicate trace IDs, which can be common with 10000s of trace ids.
        unique_trace_ids = list(set(trace_ids))
        num_duplicate_ids = len(trace_ids) - len(unique_trace_ids)
        logging.info(f"Removed {num_duplicate_ids} duplicate trace ids.")

        unprocessed_ids = self.retrieve_traces(unique_trace_ids, trace_file)
        # Check and log for potential unprocessed trace ids
        if unprocessed_ids:
            logging.warning(f"Found {len(unprocessed_ids)} unprocessed trace ids.")
            unprocessed_ids_file = log_path.joinpath('unprocessed_trace_ids.txt')
            with open(unprocessed_ids_file, 'w') as f:
                for id in unprocessed_ids:
                    f.write("%s\n" % id)

        # Inform user
        logging.info(f"Downloaded {len(trace_ids)} traces for invocations between \
{start} and {end} into {log_path}.")

    def retrieve_trace_ids(self, start, end, trace_ids_file):
        """Retrieve and save trace ids from X-Ray.
        Returns a list of trace ids."""
        # Configure trace summaries (ts) iterator using pagination
        paginator = self.client.get_paginator('get_trace_summaries')
        ts_iter = paginator.paginate(StartTime=start, EndTime=end)

        # Save trace ids to file
        trace_ids = []
        with open(trace_ids_file, 'w') as f:
            for trace_summary in ts_iter:
                batch_trace_ids = extract_trace_ids(trace_summary)
                trace_ids.extend(batch_trace_ids)
                for trace_id in batch_trace_ids:
                    f.write(f"{trace_id}\n")
        return trace_ids

    def retrieve_traces(self, unique_trace_ids, trace_file):
        """Retrieve and save full trace details in chunks from X-Ray.
        Returns a list of unprocessed trace ids.
        Output format: Every line contains a single JSON-formatted trace.
        Example output of a single trace (partial data):
        {"Id": "1-60be2454-2cb82d1221d24201751ea2e3", "Duration": 9.315, "LimitExceeded": false, "Segments": [{"Id": "050793ca38bd8ff2", "Document": "{\"id\":\"050793ca38bd8ff2\",..."}]}  # noqa: E501
        """
        unprocessed_ids = []
        with open(trace_file, 'w') as f:
            for trace_ids_batch in chunks(unique_trace_ids, 5):
                paginator = self.client.get_paginator('batch_get_traces')
                trace_iterator = paginator.paginate(TraceIds=trace_ids_batch)
                for trace_batch in trace_iterator:
                    unprocessed_ids.extend(trace_batch['UnprocessedTraceIds'])
                    for trace in trace_batch['Traces']:
                        f.write(json.dumps(trace) + '\n')
        return unprocessed_ids


def extract_trace_ids(trace_summaries):
    return [trace['Id'] for trace in trace_summaries['TraceSummaries']]


# Source: https://stackoverflow.com/a/312464/6875981
def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    return [lst[i:i + n] for i in range(0, len(lst), n)]
