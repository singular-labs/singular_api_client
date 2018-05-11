import requests
import logging

from params import Format, Dimensions, DiscrepancyMetrics, TimeBreakdown, CountryCodeFormat, Metrics
from singular_api_client.exceptions import ArgumentValidationException, APIException
from singular_api_client.helpers import ReportStatusResponse, CustomDimension, CohortMetricsResponse

logger = logging.getLogger("singular_client")


class SingularClient(object):
    BASE_API_URL = "https://api.singular.net/api/"

    def __init__(self, api_key):
        self.api_key = api_key

    def run_report(self, start_date, end_date,
                   format=Format.JSON,
                   dimensions=(Dimensions.APP, Dimensions.OS, Dimensions.SOURCE),
                   metrics=(Metrics.ADN_COST, Metrics.ADN_IMPRESSIONS),
                   discrepancy_metrics=(DiscrepancyMetrics.ADN_CLICKS, DiscrepancyMetrics.ADN_INSTALLS),
                   source=None,
                   app=None,
                   display_alignment=True,
                   time_breakdown=TimeBreakdown.ALL,
                   country_code_format=CountryCodeFormat.ISO3
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
        :param source: optional list of source names to filter by
        :param app: optional list of app names to filter by
        :param display_alignment: When set to True, results will include an alignment row to account for any difference
         between campaign and creative statistics
        :param time_breakdown: Break results by the requested time period, for example TimeBreakdown.DAY
        :param country_code_format: Country code formatting option, for example CountryCodeFormat.ISO3
        :return: report_id
        """
        query_dict = self.__build_reporting_query(start_date, end_date, format, dimensions, metrics,
                                                  discrepancy_metrics, app, source, display_alignment, time_breakdown,
                                                  country_code_format)
        response = self._api_get("v2.0/reporting", params=query_dict)
        return response

    def create_async_report(self, start_date, end_date,
                            format=Format.JSON,
                            dimensions=(Dimensions.APP, Dimensions.OS, Dimensions.SOURCE),
                            metrics=(Metrics.ADN_COST, Metrics.ADN_IMPRESSIONS),
                            discrepancy_metrics=(DiscrepancyMetrics.ADN_CLICKS, DiscrepancyMetrics.ADN_INSTALLS),
                            source=None,
                            app=None,
                            display_alignment=True,
                            time_breakdown=TimeBreakdown.ALL,
                            country_code_format=CountryCodeFormat.ISO3
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
        :param source: optional list of source names to filter by
        :param app: optional list of app names to filter by
        :param display_alignment: When set to True, results will include an alignment row to account for any difference
         between campaign and creative statistics
        :param time_breakdown: Break results by the requested time period, for example TimeBreakdown.DAY
        :param country_code_format: Country code formatting option, for example CountryCodeFormat.ISO3
        :return: report_id
        """

        query_dict = self.__build_reporting_query(start_date, end_date, format, dimensions, metrics,
                                                  discrepancy_metrics, app, source, display_alignment, time_breakdown,
                                                  country_code_format)

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
        :rtype: list(CustomDimension)
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

    @staticmethod
    def __build_reporting_query(start_date, end_date, format, dimensions, metrics, discrepancy_metrics, app,
                                source, display_alignment, time_breakdown, country_code_format):
        """
        build reporting query format that can be used by either the `create_async_report` or `reporting` endpoints
        """

        def verify_param(param_name, value, base_class):
            expected_values = base_class.__ALL_OPTIONS__
            if value not in expected_values:
                raise ArgumentValidationException("unexpected %s value %s, expected one of %s" %
                                                  (param_name, repr(value), repr(expected_values)))

        verify_param("format", format, Format)
        verify_param("time_breakdown", time_breakdown, TimeBreakdown)
        verify_param("country_code_format", country_code_format, CountryCodeFormat)

        dimensions_request = ",".join(dimensions)
        metrics_request = ",".join(metrics)
        discrepancy_metrics_request = ",".join(discrepancy_metrics)
        query_dict = dict(
            start_date=start_date,
            end_date=end_date,
            dimensions=dimensions_request,
            metrics_request=metrics_request,
            discrepancy_metrics=discrepancy_metrics_request,
            display_alignment=display_alignment,
            format=format,
            time_breakdown=time_breakdown,
            country_code_format=country_code_format
        )
        if source is not None:
            query_dict.update({'source': [",".join(source)]})
        if app is not None:
            query_dict.update({'app': [",".join(app)]})
        return query_dict

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
        headers = {"Authorization": self.api_key}

        response = requests.request(method, url, headers=headers, **kwargs)

        logger.info("%(method)s %(url)s, kwargs = %(kwargs)s, headers=%(headers)s --> code = %(code)s" %
                    dict(method=method, url=url, kwargs=repr(kwargs), code=response.status_code,
                         headers=headers))

        if not response.ok:
            raise APIException("%s failed with code = %s, payload = %s" % (
                endpoint, response.status_code, response.text))

        return response
