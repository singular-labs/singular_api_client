import requests
import logging
import json

from .params import Format, Dimensions, DiscrepancyMetrics, TimeBreakdown, CountryCodeFormat, Metrics
from .exceptions import ArgumentValidationException, APIException, UnexpectedAPIException
from .helpers import ReportStatusResponse, CustomDimension, CohortMetricsResponse, \
    DataAvailabilityResponse
from .version import __version__

logger = logging.getLogger("singular_client")


class SingularClient(object):
    """
    Client for Singular Reporting API
    See:
        - https://github.com/singular-labs/singular_api_client
        - https://developers.singular.net/v2.0/reference
    """
    BASE_API_URL = "https://api.singular.net/api/"

    def __init__(self, api_key):
        self.api_key = api_key

    def run_report(self, start_date, end_date,
                   format=Format.JSON,
                   dimensions=(Dimensions.APP, Dimensions.OS, Dimensions.SOURCE),
                   metrics=(Metrics.ADN_COST, Metrics.ADN_IMPRESSIONS),
                   discrepancy_metrics=(DiscrepancyMetrics.ADN_CLICKS, DiscrepancyMetrics.ADN_INSTALLS),
                   cohort_metrics=None,
                   cohort_periods=None,
                   source=None,
                   app=None,
                   display_alignment=True,
                   time_breakdown=TimeBreakdown.ALL,
                   country_code_format=CountryCodeFormat.ISO3,
                   filters=None
                   ):
        """
        Use this endpoint to run custom queries in the Singular platform for aggregated statistics.
          We recommend create_async_report for production ETL process

        :param start_date: "YYYY-mm-dd" format date
        :param end_date: "YYYY-mm-dd" format date
        :param format: Format for returned results, for example Format.CSV
        :param dimensions: A list of dimensions, for example [Dimensions.APP, Dimensions.Source]
        :param metrics: A list of metrics, for example [Metrics.ADN_IMPRESSIONS, Metrics.ADN_COST]
        :param discrepancy_metrics: List of metrics that may help detect discrepancies between Ad Networks
          and Attribution providers, for example [DiscrepancyMetrics.ADN_CLICKS, DiscrepancyMetrics.ADN_INSTALLS]
        :param cohort_metrics: list of cohorted metrics by name or ID; A full list can be retrieved through
          the Cohorted Metrics endpoint
        :param cohort_periods: list of cohorted periods; A full list can be retrieved through the Cohorted Metrics
          endpoint
        :param source: optional list of source names to filter by
        :param app: optional list of app names to filter by
        :param display_alignment: When set to True, results will include an alignment row to account for any difference
         between campaign and creative statistics
        :param time_breakdown: Break results by the requested time period, for example TimeBreakdown.DAY
        :param country_code_format: Country code formatting option, for example CountryCodeFormat.ISO3
        :param filters: a JSON encoded list of filters. Can be used to apply more complex filters than simply filtering
          by app or source. The relation between different elements of the list is an AND relation.
          A full list of the dimensions you can filter by and potential values can be retrieved from the
          `get_reporting_filters` endpoint.
        :return: parsed JSON response dict if format is Format.JSON or unicode if format is Format.CSV
        """
        query_dict = self.__build_reporting_query(start_date, end_date, format, dimensions, metrics,
                                                  discrepancy_metrics, cohort_metrics, cohort_periods, app,
                                                  source, display_alignment, time_breakdown, country_code_format,
                                                  filters)
        response = self._api_get("v2.0/reporting", params=query_dict)
        if format == Format.JSON:
            self.__verify_legacy_error(response.json())
            return response.json()
        elif format == Format.CSV:
            return response.text
        else:
            raise ArgumentValidationException("unsupported format")

    def create_async_report(self, start_date, end_date,
                            format=Format.JSON,
                            dimensions=(Dimensions.APP, Dimensions.OS, Dimensions.SOURCE),
                            metrics=(Metrics.ADN_COST, Metrics.ADN_IMPRESSIONS),
                            discrepancy_metrics=(DiscrepancyMetrics.ADN_CLICKS, DiscrepancyMetrics.ADN_INSTALLS),
                            cohort_metrics=None,
                            cohort_periods=None,
                            source=None,
                            app=None,
                            display_alignment=True,
                            time_breakdown=TimeBreakdown.ALL,
                            country_code_format=CountryCodeFormat.ISO3,
                            filters=None
                            ):
        """
        Use this endpoint to run custom queries in the Singular platform for aggregated statistics without keeping
         a live connection throughout the request

        :param start_date: "YYYY-mm-dd" format date
        :param end_date: "YYYY-mm-dd" format date
        :param format: Format for returned results, for example Format.CSV
        :param dimensions: A list of dimensions, for example [Dimensions.APP, Dimensions.Source]
        :param metrics: A list of metrics, for example [Metrics.ADN_IMPRESSIONS, Metrics.ADN_COST]
        :param discrepancy_metrics: List of metrics that may help detect discrepancies between Ad Networks
         and Attribution providers, for example [DiscrepancyMetrics.ADN_CLICKS, DiscrepancyMetrics.ADN_INSTALLS]
        :param cohort_metrics: list of cohorted metrics by name or ID; A full list can be retrieved through
         the Cohorted Metrics endpoint
        :param cohort_periods: list of cohorted periods; A full list can be retrieved through the Cohorted Metrics
          endpoint
        :param source: optional list of source names to filter by
        :param app: optional list of app names to filter by
        :param display_alignment: When set to True, results will include an alignment row to account for any difference
         between campaign and creative statistics
        :param time_breakdown: Break results by the requested time period, for example TimeBreakdown.DAY
        :param country_code_format: Country code formatting option, for example CountryCodeFormat.ISO3
        :param filters: a JSON encoded list of filters. Can be used to apply more complex filters than simply filtering
          by app or source. The relation between different elements of the list is an AND relation.
          A full list of the dimensions you can filter by and potential values can be retrieved from the
          `get_reporting_filters` endpoint.
        :return: report_id
        """

        query_dict = self.__build_reporting_query(start_date, end_date, format, dimensions, metrics,
                                                  discrepancy_metrics, cohort_metrics, cohort_periods, app,
                                                  source, display_alignment, time_breakdown, country_code_format,
                                                  filters)

        response = self._api_post("v2.0/create_async_report", data=query_dict)
        parsed_response = response.json()
        return parsed_response["value"]["report_id"]

    def get_report_status(self, report_id):
        """
        This endpoint returns the status of a given report.
          If a report has failed, an error message is returned. If the report completes, a download url is returned
          together with the status.

        :param report_id: id generated by the create_async_report method
        :return: return the status of the report
        :rtype: ReportStatusResponse
        """
        params = {"report_id": report_id}
        response = self._api_get("v2.0/get_report_status", params=params)
        parsed_response = response.json()
        self.__verify_legacy_error(parsed_response)
        return ReportStatusResponse(parsed_response["value"])

    def get_custom_dimensions(self):
        """
        Use this endpoint to return all the custom dimensions configured for your account by name and ID.
          Dimension IDs can then be used in Reporting API queries to group the data using Custom Dimensions

        :return: list of `CustomDimension` instances
        :rtype: list[CustomDimension]
        """
        response = self._api_get("custom_dimensions")
        parsed_response = response.json()
        self.__verify_legacy_error(parsed_response)
        return CustomDimension.parse_list(parsed_response["value"]["custom_dimensions"])

    def get_cohort_metrics(self):
        """
        Use this endpoint to return all cohorted metrics and cohort periods configured for your account

        :return: a new `CohortMetricsResponse` instance
        :rtype: CohortMetricsResponse
        """
        response = self._api_get("cohort_metrics")
        parsed_response = response.json()
        self.__verify_legacy_error(parsed_response)
        return CohortMetricsResponse(parsed_response["value"])

    def get_last_modified_dates(self, utc_timestamp, group_by_source=True):
        """
        Use this endpoint to detect retroactive data changes by source and date, to run narrowed-down queries
          using filters that only pull the modified data

        :param utc_timestamp: The UTC timestamp when you last pulled data from Singular,
            formatted as "YYYY-mm-dd HH:mm:SS"
        :type utc_timestamp: str
        :param group_by_source: When set to `True`, results will be grouped by source
        :type group_by_source: bool
        :return: List of modified dates, or dict(Network-->List of modified dates) if group_by_source=True
        :rtype: dict[str, list[str]]
        """

        query_dict = dict(timestamp=utc_timestamp, group_by_source=self.__bool(group_by_source))

        response = self._api_get("last_modified_dates", params=query_dict)
        parsed_response = response.json()
        self.__verify_legacy_error(parsed_response)
        return parsed_response["value"]["results"]

    def data_availability_status(self, data_date, format=Format.JSON, display_non_active_sources=False):
        """
        Use this endpoint to determine whether for a given day, data is available for each of your data data sources.
         This data can then be used to determine whether to pull data.

        :param data_date: You can only select a single day. The API will check whether there is data for this day.
            Date format: "YYYY-mm-dd"
        :param format: Format for returned results, for example Format.CSV
        :type format: str
        :param display_non_active_sources: Active source is defined as a source that has data in the last 30 days
        :type display_non_active_sources: bool
        :return: DataAvailabilityResponse if format==Format.JSON, or unicode if format==Format.CSV
        :rtype: DataAvailabilityResponse | unicode
        """

        self.__verify_param("format", format, Format)
        query_dict = dict(data_date=data_date, format=format,
                          display_non_active_sources=self.__bool(display_non_active_sources))

        response = self._api_get("v2.0/data_availability_status", params=query_dict)
        if format == Format.JSON:
            parsed_response = response.json()
            self.__verify_legacy_error(parsed_response)
            return DataAvailabilityResponse(parsed_response["value"])
        elif format == Format.CSV:
            return response.text
        else:
            raise ArgumentValidationException("unsupported format")

    def get_reporting_filters(self):
        """
        This endpoint returns all available filters and their respective available options.
        Please note that filters can differ between users, per the configured.

        example response:
        {
            "dimensions": [
              {
                "name": "os",
                "display_name": "OS",
                "values": [
                    {"name": 4, "display_name": "Android"},
                  {"name": 1, "display_name": "iOS"}
                ],
              },
              {
                "name": "source",
                "display_name": "Source",
                "values": [
                  {"name": "adwords", "display_name": "AdWords"}
                ]
              }
            ]
          }

        :return: dictionary of available filters and their respected values
        :rtype: dict[str, list[dict]]
        """
        response = self._api_get("v2.0/reporting/filters")
        parsed_response = response.json()
        self.__verify_legacy_error(parsed_response)
        return parsed_response["value"]

    @staticmethod
    def __bool(value):
        if value:
            return "true"
        else:
            return "false"

    @classmethod
    def __build_reporting_query(cls, start_date, end_date, format, dimensions, metrics, discrepancy_metrics,
                                cohort_metrics, cohort_periods, app, source, display_alignment, time_breakdown,
                                country_code_format, filters):
        """
        build reporting query format that can be used by either the `create_async_report` or `reporting` endpoints
        """
        cls.__verify_param("format", format, Format)
        cls.__verify_param("time_breakdown", time_breakdown, TimeBreakdown)
        cls.__verify_param("country_code_format", country_code_format, CountryCodeFormat)

        if filters is None:
            filters = []

        if (cohort_metrics or cohort_periods) and (not cohort_metrics or not cohort_periods):
            raise ArgumentValidationException("`cohort_metrics` must be used with `cohort_periods`")

        dimensions_request = ",".join(dimensions)
        metrics_request = ",".join(metrics)
        discrepancy_metrics_request = ",".join(discrepancy_metrics)
        query_dict = dict(
            start_date=start_date,
            end_date=end_date,
            dimensions=dimensions_request,
            metrics=metrics_request,
            discrepancy_metrics=discrepancy_metrics_request,
            display_alignment=display_alignment,
            format=format,
            time_breakdown=time_breakdown,
            country_code_format=country_code_format,
        )
        if source is not None:
            if not isinstance(source, list):
                sources = [source]
            else:
                sources = source
            filters.append({"dimension": "source", "operator": "in", "values": sources})
        if app is not None:
            if not isinstance(app, list):
                apps = [app]
            else:
                apps = app
            filters.append({"dimension": "app", "operator": "in", "values": apps})
        if cohort_metrics:
            query_dict.update({'cohort_metrics': [",".join(cohort_metrics)]})
        if cohort_periods:
            query_dict.update({'cohort_periods': [",".join(cohort_periods)]})
        if filters:
            query_dict["filters"] = json.dumps(filters)
        return query_dict

    @staticmethod
    def __verify_param(param_name, value, base_class):
        expected_values = base_class.__ALL_OPTIONS__
        if value not in expected_values:
            raise ArgumentValidationException("unexpected %s value %s, expected one of %s" %
                                              (param_name, repr(value), repr(expected_values)))

    @staticmethod
    def __verify_legacy_error(parsed_response):
        if parsed_response["status"] != 0:
            raise APIException("API request failed: %s" % parsed_response["value"])

    def _api_get(self, endpoint, params=None):
        return self.__api_request("GET", endpoint, params=params)

    def _api_post(self, endpoint, data=None, json=None):
        return self.__api_request("POST", endpoint, data=data, json=json)

    def __api_request(self, method, endpoint, **kwargs):
        url = self.BASE_API_URL + endpoint
        headers = {"Authorization": self.api_key,
                   'User-Agent': 'Singular API Client v%s' % __version__}

        response = requests.request(method, url, headers=headers, **kwargs)

        logger.info("%(method)s %(url)s, kwargs = %(kwargs)s --> code = %(code)s" %
                    dict(method=method, url=url, kwargs=repr(kwargs), code=response.status_code))

        if not response.ok:
            if response.status_code is None or response.status_code >= 500 < 600:
                raise UnexpectedAPIException("%s failed with code = %s, payload = %s" % (
                    endpoint, response.status_code, response.text))
            else:
                raise APIException("%s failed with code = %s, payload = %s" % (
                    endpoint, response.status_code, response.text))

        return response
