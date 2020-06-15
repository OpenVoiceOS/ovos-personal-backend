from json_database import JsonDatabase
from mock_mycroft_backend.configuration import CONFIGURATION
import json


class Metric:
    def __init__(self, metric_id, metric_type, meta="{}"):
        if isinstance(meta, str):
            meta = json.loads(meta)
        self.metric_id = metric_id
        self.metric_type = metric_type
        self.meta = meta


class JsonMetricDatabase(JsonDatabase):
    def __init__(self, path=CONFIGURATION["metrics_db"]):
        super().__init__("metrics", path)

    def add_metric(self, metric_type=None, meta="{}"):
        metric_id = self.total_metrics() + 1
        metric = Metric(metric_id, metric_type, meta)
        self.add_item(metric)

    def total_metrics(self):
        return len(self)

    def __enter__(self):
        """ Context handler """
        return self

    def __exit__(self, _type, value, traceback):
        """ Commits changes and Closes the session """
        try:
            self.commit()
        except Exception as e:
            print(e)

