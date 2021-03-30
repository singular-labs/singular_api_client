# Singular API Client Library for Python
This is the official Singular Reporting API Python Library. This library allows easy BI integration of Singular.

## Table of Contents

- [Installation](#Installation)
- [Reporting Interface Overview](#reporting-interface-overview)
- [SingularClient](#singularclient)
- [Logging](#logging)
- [ETLManager - DEPRECATED](#etl-manager---deprecated)
- [Appendix - Supported Params](#appendix---supported-params)

## Installation
The library can be installed using pip:
```
pip install singular-api-client
```

## Reporting Interface Overview

Both these classes allow requesting data using the same reporting interface, which consists of:
- `start_date` & `end_date` formatted as `YYYY-mm-dd`
- `format` - Format for returned results, supported formats include `Format.CSV` & `Format.JSON`
- `dimensions` - A list of dimensions, for example `[Dimensions.APP, Dimensions.Source]` (see full list below)
- `metrics` - A list of metrics, for example `[Metrics.ADN_IMPRESSIONS, Metrics.ADN_COST]` (see full list below)
- `discrepancy_metrics` - List of metrics that may help detect discrepancies between Ad Networks and 
    Attribution providers, for example [DiscrepancyMetrics.ADN_CLICKS, DiscrepancyMetrics.ADN_INSTALLS] (see full list below)
- `cohort_metrics` - list of cohorted metrics by name or ID; A full list can be retrieved through `SingularClient.get_cohort_metrics` method (see below)
- `cohort_periods` - list of cohorted periods; A full list can be retrieved through the `SingularClient.get_cohort_metrics` (see below)
- `source` - optional list of source names to filter by
- `app` - optional list of application names to filter by
- `display_alignment` - When set to True, results will include an alignment row to account for any difference 
    between campaign and creative statistics
- `time_breakdown` - Break results by the requested time period, for example `TimeBreakdown.DAY` (see full list below)
- `country_code_format` - Country code formatting option, supported formats include `CountryCodeFormat.ISO3` and `CountryCodeFormat.ISO`   
Note that the most up-to-date reference is documented in [Singular Reporting Endpoint](https://developers.singular.net/reference#reporting)


### Helper classes with parameter options
Most of the parameters above are lists of predefined strings, in-case you are using an IDE with auto-completion should add:
```python
from singular_api_client.params import Format, Dimensions, Metrics, DiscrepancyMetrics, CountryCodeFormat
dimensions = [Dimensions.ADN_ACCOUNT_ID, Dimensions.ADN_ORIGINAL_CURRENCY]
```    

### Dimensions
The full list of dimensions consists of:
- all of Singular built-in dimensions (see list below) 
- user-defined Custom Dimensions


#### User Defined Custom Dimensions
You can get the configured custom dimensions using `get_custom_dimensions` for example:
```python
from singular_api_client.singular_client import SingularClient
API_KEY = "YOUR API KEY"
client = SingularClient(API_KEY)
custom_dimensions = client.get_custom_dimensions()
print(custom_dimensions)
``` 

Output:
```
[<CustomDimension: Incentivized (id=8e10d3891cba7051a76062541641325b)>,
 <CustomDimension: Team (id=430164a52cdb2b9dff48b06a080a3d3f)>]
```

You can the use the returned `CustomDimension` objects or the relevant `id` when using the reporting API, for example:
```python
dimensions = [Dimensions.COUNTRY_FIELD, Dimensions.ADN_CAMPAIGN_NAME, "8e10d3891cba7051a76062541641325b"]
```

Can be configured in Singular [Custom Dimensions Configuration](https://app.singular.net/#/custom-dimensions).


### Cohort Metrics & Periods
You can get the available cohort metrics & periods by using the `get_cohort_metrics` method, for example:
```python
from singular_api_client.singular_client import SingularClient
API_KEY = "YOUR API KEY"
client = SingularClient(API_KEY)
cohort_metrics = client.get_cohort_metrics()
print("Cohort Metrics: %s" % repr(cohort_metrics))
```
Output:
```
<periods = [u'1d', u'7d', u'14d', u'30d', u'actual']>
<metrics = [
	<CohortMetric: Original Revenue (name=original_revenue)>
	<CohortMetric: ROI (name=roi)>
	<CohortMetric: ARPU (name=arpu)>
	<CohortMetric: Revenue (name=revenue)>
]>
```
 

## SingularClient
**Start with initializing a `SingularClient` object**
```python
from singular_api_client.singular_client import SingularClient
API_KEY = "YOUR API KEY"
client = SingularClient(API_KEY)
```

### Run a simple report
```python
from singular_api_client.singular_client import SingularClient
from singular_api_client.params import Format, Dimensions
API_KEY = "YOUR API KEY"
client = SingularClient(API_KEY)
start_date = "2018-03-15"
end_date = "2018-03-18"
# see [Appendix - Supported Params]
dimensions = (Dimensions.COUNTRY_FIELD, Dimensions.ADN_CAMPAIGN_NAME) 
results = client.run_report(start_date, end_date, dimensions=dimensions, format=Format.JSON)
print("Results: %s" % repr(results))
```
Output:
```
Results: {u'status': 0, u'substatus': 0, u'value': {u'results': [{u'adn_campaign_name': u'Simba_Android', u'end_date': u'2018-03-18', u'adn_installs': 97.0, u'country_field': u'DEU', u'adn_clicks': 743.0, u'start_date': u'2018-03-15'}, {u'adn_campaign_name': u'Simba_Search', u'end_date': u'2018-03-18', u'adn_installs': 95.0, u'country_field': u'GBR', u'adn_clicks': 907.0, u'start_date': u'2018-03-15'}, {u'adn_campaign_name': u'Simba iOS', u'end_date': u'2018-03-18', u'adn_installs': 194.0, u'country_field': u'CAN', u'adn_clicks': 1413.0, u'start_date': u'2018-03-15'}, {u'adn_campaign_name': u'Simba_Markets', u'end_date': u'2018-03-18', u'adn_installs': 12.0, u'country_field': u'IND', u'adn_clicks': 141.0, u'start_date': u'2018-03-15'}, {u'adn_campaign_name ...
```

### Enqueue async report
```python
from singular_api_client.singular_client import SingularClient
API_KEY = "YOUR API KEY"
client = SingularClient(API_KEY)
start_date = "2018-05-08"
end_date = "2018-05-09"
report_id = client.create_async_report(start_date, end_date)
print("Report ID: %s" % repr(report_id))
```
Output:
```
Report ID: u'd5a36f830ad305475dac28eff0e36174'
```

### Enqueue async skadnetwork raw report
```python
from singular_api_client.singular_client import SingularClient
API_KEY = "YOUR API KEY"
client = SingularClient(API_KEY)
start_date = "2021-02-01"
end_date = "2021-02-01"
dimensions = ["app", "source"]
metrics = ["skan_installs"]
report_id = client.create_async_skadnetwork_raw_report(start_date=start_date, end_date=end_date,
                                                       dimensions=dimensions, metrics=metrics)
print("Report ID: %s" % repr(report_id))
```
Output:
```
Report ID: u'f6a36f900ad305475dac28eff0e36174'
```

### Enqueue async skadnetwork report
```python
from singular_api_client.singular_client import SingularClient
API_KEY = "YOUR API KEY"
client = SingularClient(API_KEY)
start_date = "2021-02-01"
end_date = "2021-02-01"
dimensions = ["app", "source"]
metrics = ["custom_clicks", "skan_installs"]
report_id = client.create_async_skadnetwork_report(start_date=start_date, end_date=end_date,
                                                   dimensions=dimensions, metrics=metrics)
print("Report ID: %s" % repr(report_id))
```
Output:
```
Report ID: u'h7a37f800ad405475dac90eff0e36174'
```

### Check status of async report
```python
from singular_api_client.singular_client import SingularClient
API_KEY = "YOUR API KEY"
client = SingularClient(API_KEY)
report_id = "d5a36f830ad305475dac28eff0e36174"
report_status = client.get_report_status(report_id)
print("Report Status: %s" % repr(report_status))
```
Output:
```
Report Status: <ReportStatus DONE: report_id=d5a36f830ad305475dac28eff0e36174, download_url=https://singular-reports-results.s3.amazonaws.com/yourorg/d5a36f830ad305475dac28eff0e36174?Signature=XXXX&Expires=XXXX&AWSAccessKeyId=XXXX, url_expires_in=XXX>
```

### User Defined Custom Dimensions
You can get the configured custom dimensions using `get_custom_dimensions` for example:
```python
from singular_api_client.singular_client import SingularClient
API_KEY = "YOUR API KEY"
client = SingularClient(API_KEY)
custom_dimensions = client.get_custom_dimensions()
print(custom_dimensions)
``` 
Output:
```
[<CustomDimension: Incentivized (id=8e10d3891cba7051a76062541641325b)>,
 <CustomDimension: Team (id=430164a52cdb2b9dff48b06a080a3d3f)>]
```

You can the use the returned `CustomDimension` objects or the relevant `id` when using the reporting API, for example:
```python
dimensions = [Dimensions.COUNTRY_FIELD, Dimensions.ADN_CAMPAIGN_NAME, "8e10d3891cba7051a76062541641325b"]
```

Can be configured in Singular [Custom Dimensions Configuration](https://app.singular.net/#/custom-dimensions).

### SKAdNetwork Events
You can get the available SKAdNetwork events by using the `get_skan_events` method, for example:
```python
from singular_api_client.singular_client import SingularClient
API_KEY = "YOUR API KEY"
client = SingularClient(API_KEY)
skan_events = client.get_skan_events()
print("SKAdNetwork Events: %s" % repr(skan_events))
```
Output:
```
<skan_events = [
	<SkanEvent: session_count (name=b6d3h439fj3nf83jdf9dy3h4j8gh)>
	<SkanEvent: time_spent (name=c6d3h434fj3n8u3kdf9dy3h4j9dsh)>
]>
```

### Cohort Metrics & Periods
You can get the available cohort metrics & periods by using the `get_cohort_metrics` method, for example:
```python
from singular_api_client.singular_client import SingularClient
API_KEY = "YOUR API KEY"
client = SingularClient(API_KEY)
cohort_metrics = client.get_cohort_metrics()
print("Cohort Metrics: %s" % repr(cohort_metrics))
```
Output:
```
<periods = [u'1d', u'7d', u'14d', u'30d', u'actual']>
<metrics = [
	<CohortMetric: Original Revenue (name=original_revenue)>
	<CohortMetric: ROI (name=roi)>
	<CohortMetric: ARPU (name=arpu)>
	<CohortMetric: Revenue (name=revenue)>
]>
```

### Data Availability Status
Use this endpoint to determine whether for a given day, data is available for each of your data data sources.
This data can then be used to determine whether to pull data, for example:

```python
from singular_api_client.singular_client import SingularClient
API_KEY = "YOUR API KEY"
client = SingularClient(API_KEY)
data_availability_status = client.data_availability_status("2018-05-01")
print("Data Availability Status: %s" % repr(data_availability_status))
```
Output:
```
Data Availability Status: <DataAvailability: is_all_data_available=True, data_sources=see individual statuses below>
	<DataSourceAvailability: Facebook (wyatt@westworld.com) - data populated, is_available=True, last_updated_utc=2018-05-08T09:51:11, is_empty_data=False, is_active_last_30_days=True>
	<DataSourceAvailability: AdWords (wyatt@westworld.com) - data populated, is_available=True, last_updated_utc=2018-05-08T09:51:13, is_empty_data=False, is_active_last_30_days=True>
	...
```

## Logging
Logging is done with the built-in python logging library, using two loggers:
1. "etl_manager" - used by `ETLManager`
2. "singular_client" - used by `SingularClient`

For example, to enable logging of both classes to both standard-output and file:
```python
import logging
import sys

singular_api_loggers = [logging.getLogger("singular_client"), logging.getLogger("etl_manager")]
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)

file_handler = logging.FileHandler("my_log.txt")
file_handler.setFormatter(formatter)

for cur_logger in singular_api_loggers:
    cur_logger.setLevel(logging.DEBUG)
    cur_logger.addHandler(ch)
    cur_logger.addHandler(file_handler)
```  

## ETL Manager - DEPRECATED

**As of version 6.0, the ETLManager is deprecated. The last_modified_dates endpoint that it uses will also be deprecated on December 16th 2020.**  
If you want to keep using the ETLManager in the meantime, use an older version of the package.

(This change does not affect Singular's ETL product)

## Appendix - Supported Params
### Singular built-in dimensions
```python
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
    TRACKER_NAME = "tracker_name"
    RETENTION = "retention"
```


### Metrics
```python
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
```

### Discrepancy Metrics
```python
class DiscrepancyMetrics(object):
    ADN_CLICKS = "adn_clicks"
    ADN_INSTALLS = "adn_installs"
    TRACKER_CLICKS = "tracker_clicks"
    TRACKER_INSTALLS = "tracker_installs"
```
