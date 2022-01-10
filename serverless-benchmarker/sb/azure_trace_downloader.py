import logging


class AzureTraceDownloader:
    """Implements get_traces(self) to download Microsoft Azure Insights traces using
    TODO(specify which library):
    TODO(Add doc links to 'best' Azure docs)
    """

    def __init__(self, spec) -> None:
        self.spec = spec

    def get_traces(self):
        """Retrieves Azure Insights traces from the last invocation.
        """
        start, end = self.spec.event_log.get_invoke_timespan()
        log_path = self.spec.logs_directory()
        # TODO: download traces here
        num_traces = 0

        # Inform user
        logging.info(f"Downloaded {num_traces} traces for invocations between \
{start} and {end} into {log_path}.")
