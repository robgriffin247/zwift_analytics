import subprocess
import os
from pathlib import Path


def build_models(profiles_dir="."):
    """Run dbt transformations"""
    
    if os.getenv("SYSTEM")=="modal":
        cwd = Path("./modal").resolve()
        dbt_project_dir = Path("/root") 
        profiles_dir = Path("/root")
    else:        
        cwd = Path(".").resolve()
        dbt_project_dir = Path(".") 
        profiles_dir = Path(".")
    


    print(f"Running dbt from: {cwd}")

    result = subprocess.run(
        ["dbt", "build", "--profiles-dir", str(profiles_dir)],
        cwd=str(dbt_project_dir),
        capture_output=True,
        text=True,
        env=os.environ.copy(),
    )

    print(f"Return code: {result.returncode}")
    print(f"STDOUT:\n{result.stdout}")
    print(f"STDERR:\n{result.stderr}")

    if result.returncode != 0:
        raise Exception(
            f"dbt failed with return code {result.returncode}\n"
            f"STDOUT: {result.stdout}\n"
            f"STDERR: {result.stderr}"
        )

    success_count = result.stdout.count("OK created")

    return {"status": "success", "models_built": success_count, "output": result.stdout}


if __name__ == "__main__":
    print(build_models())