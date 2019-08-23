import six
import pickle
import os
import logging
import datetime
import pytz
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import requests
from retrying import retry
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


from .exceptions import retry_if_unexpected_error, UnexpectedAPIException, APIException
from .singular_client import SingularClient
from .params import Dimensions, Metrics, DiscrepancyMetrics, CountryCodeFormat, Format, TimeBreakdown


UTC_TIMEZONE = pytz.UTC

DEFAULT_DIMENSIONS = (Dimensions.APP, Dimensions.OS, Dimensions.SOURCE, Dimensions.ADN_CAMPAIGN_NAME,
                      Dimensions.ADN_CREATIVE_ID, Dimensions.ADN_CAMPAIGN_ID, Dimensions.ADN_CREATIVE_NAME,
                      Dimensions.PLATFORM, Dimensions.ADN_SUB_ADNETWORK_NAME, Dimensions.ADN_SUB_CAMPAIGN_NAME,
                      Dimensions.ADN_SUB_CAMPAIGN_ID, Dimensions.SITE_PUBLIC_ID, Dimensions.CREATIVE_IMAGE)

REPORT_TIMEOUT = 60 * 60 * 8

logger = logging.getLogger("etl_manager")

MAX_REPORTS_TO_QUEUE = 10


class State(object):
    def __init__(self):
        self.last_refresh_utc_datetime = None


class ETLManager(object):
    """
    Helps keeping your internal BI synced with Singular Reporting.

    How it works?
    ----------------------
    1. It uses the last_modified_dates endpoint to get a list of dates that were updated since the last refresh
    2. Enqueues async reports to pull the updated information
    3. Data is being stored by "Source x Date" into the data_dumps folder

    How should it be used?
    ----------------------
    This is a very naive implementation that can use as-is or
    you can inherit from this class and override `handle_new_data` method

    Basic Usage:
    ----------------------
    ```
        etl_manager = etl_manager(api_key, dimensions=[...], ...)
        while True:
            etl_manager.refresh()
            time.sleep(15*MINUTE)
    ```
    """
    STATE_LOCATION = "state.pickle"
    DEFAULT_UPDATE_WINDOW_DAYS = 30

    def __init__(self, api_key,
                 dimensions=DEFAULT_DIMENSIONS,
                 metrics=(Metrics.ADN_COST, Metrics.ADN_IMPRESSIONS),
                 discrepancy_metrics=(DiscrepancyMetrics.ADN_CLICKS, DiscrepancyMetrics.ADN_INSTALLS),
                 cohort_metrics=None,
                 cohort_periods=None,
                 display_alignment=True,
                 format=Format.JSON,
                 country_code_format=CountryCodeFormat.ISO3,
                 max_update_window_days=DEFAULT_UPDATE_WINDOW_DAYS
                 ):
        """
        Create a new instance of the ETLManager

        :param api_key: Singular Reporting API Key
        :param dimensions: A list of dimensions, for example [Dimensions.APP, Dimensions.Source]
        :param metrics: A list of metrics, for example [Metrics.ADN_IMPRESSIONS, Metrics.ADN_COST]
        :param discrepancy_metrics: List of metrics that may help detect discrepancies between Ad Networks
         and Attribution providers, for example [DiscrepancyMetrics.ADN_CLICKS, DiscrepancyMetrics.ADN_INSTALLS]
        :param cohort_metrics: list of cohorted metrics by name or ID; A full list can be retrieved through
         the Cohorted Metrics endpoint
        :param cohort_periods: list of cohorted periods; A full list can be retrieved through the Cohorted Metrics
          endpoint
        :param display_alignment: When set to True, results will include an alignment row to account for any difference
         between campaign and creative statistics
        :param format: Format for returned results, for example Format.CSV
        :param country_code_format: Country code formatting option, for example CountryCodeFormat.ISO3
        :param max_update_window_days: A cap on how much back should the script pull from Singular. Note that 
            some times data update retroactively due to historical partner reconciliation. 
            The default recommended value is %(days)d days.    
        """ % dict(days=self.DEFAULT_UPDATE_WINDOW_DAYS)
        self.client = SingularClient(api_key)
        self.dimensions = dimensions
        self.metrics = metrics
        self.discrepancy_metrics = discrepancy_metrics
        self.cohort_metrics = cohort_metrics
        self.cohort_periods = cohort_periods
        self.country_code_format = country_code_format
        self.format = format
        self.display_alignment = display_alignment
        self.max_update_window_days = max_update_window_days
        self.state = self.load_state()
        self.should_stop = False
        session = requests.Session()
        retry = Retry(
            connect=5,
            backoff_factor=0.5,
            status_forcelist=(500, 502, 504),
            method_whitelist=('GET', 'POST')
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        self.session = session

    def handle_new_data(self, source, date, download_url, report_id):
        """
        A naive implementation which download the new results and saves them under "data_dumps/source.date.format".
        For example:
            `data_dumps/Facebook.2018-05-11.json`
            or
            `data_dumps/Facebook.2018-05-11.csv`

        You should consider overriding this method to better fit your custom BI needs, for example sending the result
         to a queue for processing

        :param source: Partner Name
        :type source: str
        :param date: a date string formatted as "%Y-%m-%d"
        :type date: str
        :param download_url: URL to download the report
        :type date: str
        :param report_id: Singular Internal Report ID, can be used for auditing
        :type date: str
        """
        r = self.session.get(download_url)
        if not r.ok:
            if r.status_code is None or (500 <= r.status_code < 600):
                raise UnexpectedAPIException("unexpected error when downloading report_id=%s, url=%s" % (
                    report_id, download_url))
            else:
                raise APIException("downloading report failed for report_id=%s, url=%s" % (
                    report_id, download_url))

        logger.info("saving data for source = %s, date = %s (report_id=%s)" % (source, date, report_id))
        output_file = open("data_dumps/%s.%s.%s" % (source, date, self.format), 'wb')
        output_file.write(r.content)
        output_file.close()

    def refresh(self):
        """
        Call this method every time you want to sync your BI with Singular
        """
        next_timestamp = datetime.datetime.now(UTC_TIMEZONE)
        reports_to_run = self._get_reports_to_queue()

        logger.info("Adding %d reports to the queue" % len(reports_to_run))
        pool = ThreadPoolExecutor(MAX_REPORTS_TO_QUEUE)

        futures = [pool.submit(self.run_async_report, source, date) for (source, date) in reports_to_run]
        complete_counter = 0
        try:
            for r in as_completed(futures, timeout=REPORT_TIMEOUT):
                _ = r.result()
                complete_counter += 1
                logger.info("Got result for report #%d out of a total of %d" % (complete_counter, len(reports_to_run)))
        except Exception:
            self.should_stop = True
            logger.exception("failed executing future, stopping everything now")
            raise
        logger.info("successfully downloaded %d reports" % len(reports_to_run))

        self.state.last_refresh_utc_datetime = next_timestamp
        self.save_state()

        return reports_to_run

    def load_state(self):
        """
        Load a previous state which includes the last refresh timestamp

        :return: Loaded State object
        :rtype: State
        """
        if os.path.exists(self.STATE_LOCATION):
            logger.info("loading existing state")
            return pickle.load(open(self.STATE_LOCATION, 'rb'))
        else:
            logger.info("no state found, creating a new state")
            return State()

    def save_state(self):
        """
        Commit the current state to disk
        """
        logger.info("Saving state")
        pickle.dump(self.state, open(self.STATE_LOCATION, 'wb'))
        return

    @retry(wait_exponential_multiplier=1000, wait_exponential_max=60000,
           retry_on_exception=retry_if_unexpected_error, stop_max_attempt_number=10)
    def run_async_report(self, source, date):
        """
        Enqueue and Poll one report from Singular API (using the async endpoint)
        Note: This method doesn't have any return value and should raise an Exception in case of failure

        :param source: Partner name
        :param date: requested date formatted in "%Y-%m-%d"
        """
        if self.should_stop:
            logger.debug("stopping now")
            return
        reports_queue_time = time.time()
        report_id = self.client.create_async_report(start_date=date,
                                                    end_date=date,
                                                    format=self.format,
                                                    dimensions=self.dimensions,
                                                    metrics=self.metrics,
                                                    discrepancy_metrics=self.discrepancy_metrics,
                                                    cohort_metrics=self.cohort_metrics,
                                                    cohort_periods=self.cohort_periods,
                                                    source=[source],
                                                    time_breakdown=TimeBreakdown.DAY,
                                                    country_code_format=self.country_code_format,
                                                    display_alignment=self.display_alignment
                                                    )
        while True:
            if self.should_stop:
                logger.info("run_async_report: interrupting report_id = %s" % report_id)
                return
            report_status = self.client.get_report_status(report_id)
            running_for = time.time() - reports_queue_time
            if report_status.status in [report_status.QUEUED, report_status.STARTED]:
                logger.info(
                    "waiting for report source = %s, date = %s, status = %s\n report_id = %s, queued %d seconds ago" %
                    (source, date, report_status.status, report_id, running_for))
                time.sleep(10)
            else:
                break

        if report_status.status != report_status.DONE:
            raise Exception("running report failed for source = %s, date = %s: %s" %
                            (source, date, repr(report_status)))

        # Process the new report
        self.handle_new_data(source, date, report_status.download_url, report_id)

    @staticmethod
    def _encode_timestamp_to_date(timestamp):
        return timestamp.strftime("%Y-%m-%d")

    def _get_reports_to_queue(self):
        """
        Builds a list of (source, date) tuples that needs to be queried.

        :return: list of (source, date) tuples, for example [("AdWords", "2018-08-01"), ...]
        :rtype: list[(str, str)]
        """
        last_modified_timestamp = self.state.last_refresh_utc_datetime
        min_date = datetime.datetime.now() - datetime.timedelta(days=self.max_update_window_days)
        reports_to_run = []

        if last_modified_timestamp is None:
            logger.info("This is the first time we pull data, so we can't use the `last_modified_dates` endpoint")
            max_date = datetime.datetime.now()
            logger.info("Run a one-time [Source x Date] report to find out which reports to pull")
            results = self.client.run_report(start_date=self._encode_timestamp_to_date(min_date),
                                             end_date=self._encode_timestamp_to_date(max_date),
                                             format=Format.JSON,
                                             dimensions=[Dimensions.SOURCE],
                                             metrics=self.metrics,
                                             discrepancy_metrics=self.discrepancy_metrics,
                                             cohort_metrics=self.cohort_metrics,
                                             cohort_periods=self.cohort_periods,
                                             time_breakdown=TimeBreakdown.DAY,
                                             country_code_format=self.country_code_format,
                                             display_alignment=self.display_alignment
                                             )

            for row in results["value"]["results"]:
                reports_to_run.append((row[Dimensions.SOURCE], row[Dimensions.START_DATE]))
        else:
            utc_timestamp = last_modified_timestamp.strftime("%Y-%m-%d %H:%M:%S")
            logger.info("Querying last_modified_dated since %s" % last_modified_timestamp)
            last_modified = self.client.get_last_modified_dates(utc_timestamp,
                                                                group_by_source=True)
            for source, dates in six.iteritems(last_modified):
                logger.info("updating %s, %d dates to update" % (source, len(dates)))
                for date in dates:
                    parsed_date = datetime.datetime.strptime(date, "%Y-%m-%d")
                    if parsed_date < min_date:
                        logger.info("%s - skipping date %s since it's outside update window" % (source, parsed_date))
                    else:
                        reports_to_run.append((source, date))

        return reports_to_run
