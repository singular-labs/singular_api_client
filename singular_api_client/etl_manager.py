import six
import pickle
import os
import logging
import datetime
import pytz
import gevent.pool
import gevent.monkey
import gevent.timeout
import time
import requests

from singular_client import SingularClient
from params import Dimensions, Metrics, DiscrepancyMetrics, CountryCodeFormat, Format, TimeBreakdown

DEFAULT_DIMENSIONS = (Dimensions.APP, Dimensions.OS, Dimensions.SOURCE, Dimensions.ADN_CAMPAIGN_NAME,
                      Dimensions.ADN_CREATIVE_ID, Dimensions.ADN_CAMPAIGN_ID, Dimensions.ADN_CREATIVE_NAME,
                      Dimensions.PLATFORM, Dimensions.ADN_SUB_ADNETWORK_NAME, Dimensions.ADN_SUB_CAMPAIGN_NAME,
                      Dimensions.ADN_SUB_CAMPAIGN_ID, Dimensions.SITE_PUBLIC_ID, Dimensions.CREATIVE_IMAGE)

REPORT_TIMEOUT = 60 * 10

STATE_LOCATION = "state.pickle"
logger = logging.getLogger("etl_manager")
gevent.monkey.patch_all()

MAX_UPDATE_WINDOW_DAYS = 7
MAX_REPORTS_TO_QUEUE = 5


class State(object):
    def __init__(self):
        self.last_refresh_utc_datetime = datetime.datetime(2018, 1, 1, tzinfo=pytz.UTC)


class ETLManager(object):
    """
    Helps keeping your internal BI synced with Singular Reporting
    """

    def __init__(self, api_key,
                 dimensions=DEFAULT_DIMENSIONS,
                 metrics=(Metrics.ADN_COST, Metrics.ADN_IMPRESSIONS),
                 discrepancy_metrics=(DiscrepancyMetrics.ADN_CLICKS, DiscrepancyMetrics.ADN_INSTALLS),
                 cohort_metrics=None,
                 cohort_periods=None,
                 country_code_format=CountryCodeFormat.ISO3
                 ):
        self.client = SingularClient(api_key)
        self.dimensions = dimensions
        self.metrics = metrics
        self.discrepancy_metrics = discrepancy_metrics
        self.cohort_metrics = cohort_metrics
        self.cohort_periods = cohort_periods
        self.country_code_format = country_code_format
        self.state = self.load_state()

    def load_state(self):
        if os.path.exists(STATE_LOCATION):
            logger.info("loading existing state")
            return pickle.load(file(STATE_LOCATION, 'rb'))
        else:
            logger.info("no state found, creating a new state")
            return State()

    def save_state(self):
        logger.info("Saving state")
        pickle.dump(self.state, file(STATE_LOCATION, 'wb'))
        return

    def run_async_report(self, source, date):
        report_id = self.client.create_async_report(start_date=date,
                                                    end_date=date,
                                                    format=Format.CSV,
                                                    dimensions=self.dimensions,
                                                    metrics=self.metrics,
                                                    discrepancy_metrics=self.discrepancy_metrics,
                                                    cohort_metrics=self.cohort_metrics,
                                                    cohort_periods=self.cohort_periods,
                                                    source=[source],
                                                    time_breakdown=TimeBreakdown.DAY,
                                                    country_code_format=self.country_code_format
                                                    )
        while True:
            report_status = self.client.get_report_status(report_id)
            if report_status.status in [report_status.QUEUED, report_status.STARTED]:
                logger.info("waiting for report source = %s, date = %s" % (source, date))
                time.sleep(10)
            else:
                break

        if report_status.status != report_status.DONE:
            raise Exception("running report failed for source = %s, date = %s: %s" %
                            (source, date, repr(report_status)))

        # download report
        result = requests.get(report_status.download_url)
        self.handle_new_date(source, date, result.text)
        return len(result.text)

    def handle_new_date(self, source, date, data):
        logger.info("saving data for  source = %s, date = %s" % (source, date))
        output_file = open("data_dumps/%s.%s.csv" % (source, date), 'wb')
        output_file.write(data)
        output_file.close()

    def refresh(self):
        last_modified_timestamp = self.state.last_refresh_utc_datetime
        utc_timestamp = last_modified_timestamp.strftime("%Y-%m-%d %H:%M:%S")
        next_timestamp = datetime.datetime.now(pytz.UTC)

        logger.info("Querying last_modified_dated since %s" % last_modified_timestamp)

        last_modified = self.client.get_last_modified_dates(utc_timestamp,
                                                            group_by_source=True)

        min_date = datetime.datetime.now() - datetime.timedelta(days=MAX_UPDATE_WINDOW_DAYS)
        reports_to_run = []
        for source, dates in six.iteritems(last_modified):
            logger.info("updating %s, %d dates to update" % (source, len(dates)))
            for date in dates:
                parsed_date = datetime.datetime.strptime(date, "%Y-%m-%d")
                if parsed_date < min_date:
                    logger.info("%s - skipping date %s since it's outside update window" % (source, parsed_date))
                else:
                    reports_to_run.append((source, date))

        logger.info("Adding %d reports to the queue" % len(reports_to_run))
        pool = gevent.pool.Pool(MAX_REPORTS_TO_QUEUE)

        def gevent_async_report(report_tuple):
            source, date = report_tuple
            return gevent.timeout.with_timeout(REPORT_TIMEOUT, self.run_async_report, source, date)

        bytes_downloaded = list(pool.imap_unordered(gevent_async_report, reports_to_run))
        logger.info("downloaded a total of %d bytes" % sum(bytes_downloaded))

        self.state.last_refresh_utc_datetime = next_timestamp
        self.save_state()

        return reports_to_run
