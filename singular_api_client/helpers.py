import json


class ReportStatusResponse(object):
    QUEUED = "QUEUED"
    STARTED = "STARTED"
    DONE = "DONE"
    FAILED = "FAILED"

    def __init__(self, response_value):
        self.report_id = response_value["report_id"]
        self.status = response_value["status"]
        self.url_expires_in = response_value.get("url_expires_in")
        self.download_url = response_value.get("download_url")
        self.error_message = response_value.get("error_message")
        self._original = response_value

    def __repr__(self):
        base = "<ReportStatus %(status)s: report_id=%(report_id)s" % dict(status=self.status, report_id=self.report_id)
        parts = [base]
        if self.status == self.DONE:
            parts.append("download_url=%(download_url)s, url_expires_in=%(expries)s" % \
                         dict(download_url=self.download_url, expries=self.url_expires_in))
        elif self.status == self.FAILED:
            parts.append("error_message=%(error_message)s" % dict(error_message=self.error_message))
        final = ", ".join(parts) + ">"
        return final

    def __str__(self):
        return json.dumps(self._original)


class CustomDimension(object):
    def __init__(self, display_name, id):
        self.display_name = display_name
        self.id = id

    @staticmethod
    def parse_list(list_from_endpoint):
        """
        helper method to parse custom dimensions list from the `custom_dimensions` endpoint
        :rtype: list[CustomDimension]
        """
        ret = []
        for value in list_from_endpoint:
            ret.append(CustomDimension(value["display_name"], value["id"]))
        return ret

    def __repr__(self):
        return "<CustomDimension: %(display_name)s (id=%(id)s)>" % dict(display_name=self.display_name,
                                                                        id=self.id)

    def __str__(self):
        return self.id


class CohortMetric(object):
    def __init__(self, display_name, name):
        self.display_name = display_name
        self.name = name

    @staticmethod
    def parse_list(list_from_endpoint):
        """
        helper method to parse custom dimensions list from the `cohort_metrics` endpoint
        :rtype: list[CohortMetric]
        """
        ret = []
        for value in list_from_endpoint:
            ret.append(CohortMetric(value["display_name"], value["name"]))
        return ret

    def __repr__(self):
        return "<CohortMetric: %(display_name)s (name=%(name)s)>" % dict(display_name=self.display_name,
                                                                         name=self.name)

    def __str__(self):
        return self.name


class CohortMetricsResponse(object):
    def __init__(self, value_from_endpoint):
        self.periods = value_from_endpoint["periods"]
        self.metrics = CohortMetric.parse_list(value_from_endpoint["metrics"])

    def __repr__(self):
        return "<Periods: %s, Metrics: %s>" % (self.periods, [repr(i) for i in self.metrics])