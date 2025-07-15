from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
from orchestration import ScraperOrchestrator

def run_etimad_pipeline():
    orchestrator = ScraperOrchestrator()
    import asyncio
    asyncio.run(orchestrator.run_pipeline())

default_args = {
    'owner': 'etimad',
    'retries': 1,
    'retry_delay': timedelta(minutes=10)
}

with DAG(
    dag_id="etimad_scraper_dag",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule_interval="@daily",
    catchup=False
) as dag:
    scrape_task = PythonOperator(
        task_id="run_etimad_scraper",
        python_callable=run_etimad_pipeline
    )
