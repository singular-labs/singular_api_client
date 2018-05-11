class Dimensions(object):
    APP = "app"
    SOURCE = "source"
    OS = "os"
    # TODO: add all dimensions


class Metrics(object):
    ADN_IMPRESSIONS = "adn_impressions"
    ADN_COST = "adn_cost"
    # TODO: add all metrics


class DiscrepancyMetrics(object):
    ADN_CLICKS = "adn_clicks"
    ADN_INSTALLS = "adn_installs"
    # TODO: add all metrics


class TimeBreakdown(object):
    ALL = "all"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"

    __ALL_OPTIONS__ = None


TimeBreakdown.__ALL_OPTIONS__ = [TimeBreakdown.ALL, TimeBreakdown.DAY, TimeBreakdown.WEEK, TimeBreakdown.MONTH]


class CountryCodeFormat(object):
    ISO3 = "iso3"
    ISO = "iso"

    __ALL_OPTIONS__ = None


CountryCodeFormat.__ALL_OPTIONS__ = [CountryCodeFormat.ISO, CountryCodeFormat.ISO3]


class Format(object):
    JSON = "json"
    CSV = "csv"

    __ALL_OPTIONS__ = None


Format.__ALL_OPTIONS__ = [Format.JSON, Format.CSV]