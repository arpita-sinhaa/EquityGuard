from google.cloud import bigquery
from config import FULL_TABLE

class BigQueryClient:
    def __init__(self):
        self.client = bigquery.Client()

    def insert_rows(self, rows):
        return self.client.insert_rows_json(FULL_TABLE, rows)

    def run_query(self, query):
        return self.client.query(query).to_dataframe()

bq_client = BigQueryClient()