# singular_api_client
Python Library Helper for Singular Reporting API

# Basic API Usage
## Init client object
```client = SingularClient(API_KEY)```

## Run report
```python
from singular_api_client import SingularClient
API_KEY = "YOUR API KEY"
client = SingularClient(API_KEY)
start_date = "2018-05-08"
end_date = "2018-05-09"
results = client.run_report(start_date, end_date)
print("Results: %s" % repr(results))
```

## Enqueue async report
```python
from singular_api_client import SingularClient
API_KEY = "YOUR API KEY"
client = SingularClient(API_KEY)
start_date = "2018-05-08"
end_date = "2018-05-09"
report_id = client.create_async_report(start_date, end_date)
print("Report ID: %s" % repr(report_id))
```

## Check status of async report
```python
from singular_api_client import SingularClient
API_KEY = "YOUR API KEY"
client = SingularClient(API_KEY)
report_id = "1234abcdef1234abcdef1234abcdef"
report_status = client.get_report_status(report_id)
print("Report Status: %s" % repr(report_status))
```


## Get Custom Dimensions
```python
from singular_api_client import SingularClient
API_KEY = "YOUR API KEY"
client = SingularClient(API_KEY)
custom_dimensions = client.get_custom_dimensions()
print("custom dimensions: %s" % repr(custom_dimensions))
```

## Get Cohort Metrics
```python
from singular_api_client import SingularClient
API_KEY = "YOUR API KEY"
client = SingularClient(API_KEY)
cohort_metrics = client.get_cohort_metrics()
print("Cohort Metrics: %s" % repr(cohort_metrics))
```


# ETL Manager
For now you need to check the interface and implement your own instance.
```python
import logging
import sys
from singular_api_client.etl_manager import ETLManager
import time

API_KEY = "[API_KEY]"


logger = logging.getLogger("singular_client")
logger2 = logging.getLogger("etl_manager")
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.setLevel(logging.DEBUG)
logger.addHandler(ch)

logger2.setLevel(logging.DEBUG)
logger2.addHandler(ch)


def main():
    etl_manager = ETLManager(API_KEY)

    while True:
        etl_manager.refresh()
        time.sleep(15*60)


if __name__ == "__main__":
        main()

```