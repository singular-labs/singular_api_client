class Dimensions(object):
    APP = "app"
    SOURCE = "source"
    OS = "os"
    SITE_PUBLIC_ID = "site_public_id"
    PLATFORM = "platform"
    COUNTRY_FIELD = "country_field"
    ADN_CAMPAIGN_NAME = "adn_campaign_name"
    ADN_CAMPAIGN_ID = "adn_campaign_id"
    SINGULAR_CAMPAIGN_ID = "singular_campaign_id"
    ADN_SUB_CAMPAIGN_NAME = "adn_sub_campaign_name"
    ADN_SUB_CAMPAIGN_ID = "adn_sub_campaign_id"
    ADN_SUB_ADNETWORK_NAME = "adn_sub_adnetwork_name"
    ADN_ORIGINAL_CURRENCY = "adn_original_currency"
    ADN_TIMEZONE = "adn_timezone"
    ADN_UTC_OFFSET = "adn_utc_offset"
    ADN_ACCOUNT_ID = "adn_account_id"
    ADN_CAMPAIGN_URL = "adn_campaign_url"
    ADN_STATUS = "adn_status"
    ADN_CLICK_TYPE = "adn_click_type"
    KEYWORD = "keyword"
    KEYWORD_ID = "keyword_id"
    PUBLISHER_ID = "publisher_id"
    PUBLISHER_SITE_ID = "publisher_site_id"
    PUBLISHER_SITE_NAME = "publisher_site_name"
    ADN_PUBLISHER_ID = "adn_publisher_id"

    ADN_CREATIVE_NAME = "adn_creative_name"
    ADN_CREATIVE_ID = "adn_creative_id"
    SINGULAR_CREATIVE_ID = "singular_creative_id"
    CREATIVE_HASH = "creative_hash"
    CREATIVE_IMAGE_HASH = "creative_image_hash"
    CREATIVE_IMAGE = "creative_image"
    CREATIVE_TEXT = "creative_text"
    CREATIVE_URL = "creative_url"
    CREATIVE_WIDTH = "creative_width"
    CREATIVE_HEIGHT = "creative_height"
    CREATIVE_IS_VIDEO = "creative_is_video"

    CAMPAIGN_STATUS = "campaign_status"
    STANDARDIZED_BID_STRATEGY = "standardized_bid_strategy"
    BID_STRATEGY = "bid_strategy"
    STANDARDIZED_BID_TYPE = "standardized_bid_type"
    BID_TYPE = "bid_type"
    CAMPAIGN_OBJECTIVE = "campaign_objective"
    BID_AMOUNT = "bid_amount"
    ORIGINAL_BID_AMOUNT = "original_bid_amount"
    ORIGINAL_METADATA_CURRENCY = "original_metadata_currency"
    MIN_ROAS = "min_roas"

    TRACKER_NAME = "tracker_name"
    RETENTION = "retention"
    START_DATE = "start_date"
    END_DATE = "end_date"


class Metrics(object):
    ADN_IMPRESSIONS = "adn_impressions"
    ADN_COST = "adn_cost"
    ADN_ORIGINAL_COST = "adn_original_cost"
    ADN_ESTIMATED_TOTAL_CONVERSIONS = "adn_estimated_total_conversions"
    CUSTOM_CLICKS = "custom_clicks"
    CUSTOM_INSTALLS = "custom_installs"
    CTR = "ctr"
    CVR = "cvr"
    ECPI = "ecpi"
    OCVR = "ocvr"
    ECPM = "ecpm"
    ECPC = "ecpc"


class DiscrepancyMetrics(object):
    ADN_CLICKS = "adn_clicks"
    ADN_INSTALLS = "adn_installs"
    TRACKER_CLICKS = "tracker_clicks"
    TRACKER_INSTALLS = "tracker_installs"


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
