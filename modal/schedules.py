import modal
from jobs import refresh_riders_job, get_event_results_job
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

IMAGE = (
    modal.Image.debian_slim()
    .pip_install_from_pyproject(
        PROJECT_ROOT / "pyproject.toml",
    )
    # modal code
    .add_local_file(PROJECT_ROOT / "modal/jobs.py", "/root/jobs.py")
    # ingestion code
    .add_local_dir(PROJECT_ROOT / "ingestion", "/root/ingestion")
)

dlt_volume = modal.Volume.from_name("zwift-analytics-dlt-state", create_if_missing=True)

SECRETS = [modal.Secret.from_name("zwift-analytics-secret")]
VOLUMES = {"/root/.dlt": dlt_volume}
TIMEOUT = 3200
RETRIES = 2

app = modal.App("zwift-analytics-scheduled-jobs", image=IMAGE)

@app.function(
    schedule=modal.Cron("0 3 * * *"),
    secrets=SECRETS,
    volumes=VOLUMES,
    timeout=TIMEOUT,
    retries=RETRIES,
)
def daily_3am():
    refresh_riders_job()
    dlt_volume.commit()
    print("Volume commited")


@app.function(
    schedule=modal.Cron("5,25,45 * * * *"),
    secrets=SECRETS,
    volumes=VOLUMES,
    timeout=TIMEOUT,
    retries=RETRIES,
)
def every_20_minutes():
    get_event_results_job()
    dlt_volume.commit()
    print("Volume commited")
