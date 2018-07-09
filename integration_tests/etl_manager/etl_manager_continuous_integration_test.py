import click
import time
from singular_api_client.etl_manager import ETLManager
from singular_api_client.params import Dimensions, Metrics, Format, DiscrepancyMetrics, TimeBreakdown
from singular_api_client.singular_client import SingularClient
import logging
import pytz
import datetime
import sys
import glob
import json
from collections import defaultdict

ONE_HOUR = 60 * 60
TIMEZONE = pytz.timezone("US/Pacific")
all_loggers = [logging.getLogger("singular_client"),
               logging.getLogger("etl_manager"),
               logging.getLogger("accuracy_check")]
logger = logging.getLogger("accuracy_check")


compare_metrics = [Metrics.ADN_COST, Metrics.ADN_IMPRESSIONS, Metrics.CUSTOM_CLICKS, Metrics.CUSTOM_INSTALLS]
compare_discrepancy_metrics = [
    DiscrepancyMetrics.TRACKER_INSTALLS,
    DiscrepancyMetrics.TRACKER_CLICKS,
    DiscrepancyMetrics.ADN_INSTALLS,
    DiscrepancyMetrics.ADN_CLICKS]

dimensions = [Dimensions.APP,
              Dimensions.SITE_PUBLIC_ID,
              Dimensions.SOURCE,
              Dimensions.OS,
              Dimensions.PLATFORM,
              Dimensions.COUNTRY_FIELD,
              Dimensions.ADN_CAMPAIGN_NAME,
              Dimensions.ADN_CAMPAIGN_ID,
              Dimensions.SINGULAR_CAMPAIGN_ID,
              Dimensions.ADN_SUB_CAMPAIGN_NAME,
              Dimensions.ADN_SUB_CAMPAIGN_ID,
              Dimensions.ADN_PUBLISHER_ID,
              Dimensions.PUBLISHER_SITE_ID,
              Dimensions.PUBLISHER_SITE_NAME,
              Dimensions.ADN_SUB_ADNETWORK_NAME,
              Dimensions.ADN_ORIGINAL_CURRENCY,
              Dimensions.ADN_TIMEZONE,
              Dimensions.ADN_UTC_OFFSET,
              Dimensions.ADN_ACCOUNT_ID,
              Dimensions.ADN_CAMPAIGN_URL,
              Dimensions.ADN_STATUS,
              Dimensions.ADN_CLICK_TYPE,
              Dimensions.TRACKER_NAME,
              Dimensions.RETENTION,
              Dimensions.KEYWORD,
              ]

metrics = [
    Metrics.ADN_IMPRESSIONS,
    Metrics.CUSTOM_INSTALLS,
    Metrics.CUSTOM_CLICKS,
    Metrics.ADN_COST,
    Metrics.ADN_ESTIMATED_TOTAL_CONVERSIONS,
    Metrics.ADN_ORIGINAL_COST,
    Metrics.CTR,
    Metrics.CVR,
    Metrics.ECPI,
    Metrics.OCVR,
    Metrics.ECPM,
    Metrics.ECPC]

discrepancy_metrics = [DiscrepancyMetrics.ADN_CLICKS,
                       DiscrepancyMetrics.ADN_INSTALLS,
                       DiscrepancyMetrics.TRACKER_CLICKS,
                       DiscrepancyMetrics.TRACKER_INSTALLS]

def encode_date(timestamp):
    if isinstance(timestamp, str):
        return timestamp
    else:
        return ETLManager._encode_timestamp_to_date(timestamp)


def daterange(start_date, end_date):
    cur_date = start_date
    while cur_date <= end_date:
        yield cur_date
        cur_date = cur_date + datetime.timedelta(days=1)


def configure_logging(loggers, log_file_template="accuracy_check.%Y-%m-%d.log"):
    """
    configure basic logging
    """
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    now = datetime.datetime.now(TIMEZONE)

    current_log_file = now.strftime(log_file_template)

    file_handler = logging.FileHandler(current_log_file)
    file_handler.setFormatter(formatter)

    for cur_logger in loggers:
        cur_logger.setLevel(logging.DEBUG)
        cur_logger.addHandler(ch)
        cur_logger.addHandler(file_handler)


all_metrics_to_check = compare_discrepancy_metrics + compare_metrics
configure_logging(all_loggers)


def get_dumped_total_per_source_date(start_date, end_date):
    source_date2metrics = defaultdict(lambda: {i: 0.0 for i in all_metrics_to_check})
    for cur_date in daterange(start_date, end_date):
        files = glob.glob("data_dumps/*.%s.json" % encode_date(cur_date))
        for file_path in files:
            data = json.loads(open(file_path, 'rb').read().decode("utf8"))
            for row in data["results"]:
                for metric in all_metrics_to_check:
                    cur_dict = source_date2metrics[(row[Dimensions.START_DATE], row[Dimensions.SOURCE])]
                    cur_dict[metric] += row[metric] if row[metric] else 0
    return dict(source_date2metrics)


def accuracy_check(api_key, start_date, end_date):
    client = SingularClient(api_key)
    logger.info("running accuracy check: %s -> %s" % (start_date, end_date))
    local_totals = get_dumped_total_per_source_date(start_date, end_date)

    results = client.run_report(encode_date(start_date),
                                encode_date(end_date),
                                format=Format.JSON,
                                dimensions=[Dimensions.SOURCE],
                                metrics=compare_metrics,
                                discrepancy_metrics=compare_discrepancy_metrics,
                                time_breakdown=TimeBreakdown.DAY
                                )
    issues = []
    for row in results["value"]["results"]:
        cur_date = row[Dimensions.START_DATE]
        cur_source = row[Dimensions.SOURCE]
        cur_local_totals = local_totals[(cur_date, cur_source)]
        server_totals = {metric: row[metric] for metric in all_metrics_to_check}
        for metric in all_metrics_to_check:
            server_value = server_totals[metric] if server_totals[metric] else 0
            delta = abs(cur_local_totals[metric] - server_value)
            if delta > 10 and delta / float(server_value) > 0.05:
                issue = (cur_date, cur_source, metric, cur_local_totals[metric], server_value)
                issues.append(issue)
                logger.error("found issue on %s, %s, %s (local %d != server %d)" % issue)
    if len(issues):
        logger.error("found %d issues" % len(issues))
    else:
        logger.info("no issues were found between %s -> %s" % (start_date, end_date))


@click.command("etl_continuous_test")
@click.argument("api_key", envvar='API_KEY')
@click.option("--days-back", default=30, type=int)
def etl_continuous_test(api_key, days_back):
    manager = ETLManager(api_key,
                         dimensions=dimensions,
                         metrics=metrics,
                         discrepancy_metrics=discrepancy_metrics,
                         format=Format.JSON,
                         max_update_window_days=days_back)
    while True:
        manager.refresh()
        start_date = datetime.date.today() - datetime.timedelta(days=days_back)
        end_date = datetime.date.today() - datetime.timedelta(days=1)
        accuracy_check(api_key, start_date, end_date)
        logger.info("sleeping for one hour")
        time.sleep(ONE_HOUR)


if __name__ == "__main__":
    etl_continuous_test()
