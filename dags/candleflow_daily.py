"""CandleFlow daily DAG: load one day of Coinbase candles into the warehouse."""

from datetime import datetime, timedelta, timezone

from airflow.sdk import dag, task


@dag(
    dag_id="candleflow_daily",
    schedule="@daily",
    start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
    catchup=False,
    tags=["candleflow"],
)
def candleflow_daily():
    @task
    def extract_load(data_interval_start=None, run_id=None) -> int:
        # Imported here, not at the top, so the DAG file stays cheap to parse.
        from ingestion.pipeline import DEFAULT_PRODUCTS, load_range

        # A run with no data interval (e.g. a manual trigger) loads yesterday.
        day = data_interval_start or datetime.now(timezone.utc) - timedelta(days=1)
        start = datetime(day.year, day.month, day.day, tzinfo=timezone.utc)
        end = start + timedelta(days=1) - timedelta(seconds=1)  # 23:59:59 the same day

        return load_range(DEFAULT_PRODUCTS, start, end, run_id=f"airflow-{run_id}")

    extract_load()


candleflow_daily()