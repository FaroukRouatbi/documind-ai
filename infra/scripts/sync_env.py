import argparse
import json
import subprocess
from pathlib import Path

import psycopg
from cognito_bootstrap import TEST_TENANT_ID, bootstrap_test_user


def parse_args():
    parser = argparse.ArgumentParser(
        description="Sync Terraform outputs into a local .env file"
    )
    parser.add_argument(
        "--env-dir",
        default="../environments/dev",
        help="Path to the Terraform environment directory (default: ../environments/dev)",
    )
    parser.add_argument(
        "--env-file",
        default="../../backend/api/.env",
        help="Path to the .env file (default: ../../backend/api/.env)",
    )
    return parser.parse_args()


def get_terraform_outputs(env_dir: str) -> dict:
    result = subprocess.run(
        ["terraform", "output", "-json"],
        cwd=env_dir,
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


ENV_TO_TF_OUTPUT = {
    "COGNITO_USER_POOL_ID": "cognito_user_pool_id",
    "COGNITO_USER_POOL_CLIENT_ID": "cognito_user_pool_client_id",
    "DOCUMENTS_BUCKET_NAME": "documents_bucket_name",
    "SQS_QUEUE_URL": "sqs_queue_url",
}


def update_env_file(env_path: Path, tf_outputs: dict, mapping: dict) -> None:
    lines = env_path.read_text().splitlines()
    updated_lines = []

    for line in lines:
        matched = False
        for env_key, tf_key in mapping.items():
            if line.startswith(f"{env_key}="):
                fresh_value = tf_outputs[tf_key]["value"]
                updated_lines.append(f"{env_key}={fresh_value}")
                print(f"Updated {env_key}")
                matched = True
                break
        if not matched:
            updated_lines.append(line)

    env_path.write_text("\n".join(updated_lines) + "\n")


def ensure_app_role() -> None:
    conn = psycopg.connect(
        host="localhost",
        port=5433,
        dbname="documind",
        user="documind",
        password="localdev",
    )
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_roles WHERE rolname = 'documind_app'")
        exists = cur.fetchone() is not None
        if exists:
            print("documind_app role already exists, skipping")
        else:
            cur.execute(
                "CREATE ROLE documind_app WITH LOGIN PASSWORD %s",
                ("local_dev_app_pw_2026",),
            )
            cur.execute("GRANT USAGE ON SCHEMA public TO documind_app")
            cur.execute(
                "GRANT SELECT, INSERT, UPDATE, DELETE ON documents, tenants TO documind_app"
            )
            print("Created documind_app role with grants")
    conn.close()


def ensure_test_tenant() -> None:
    conn = psycopg.connect(
        host="localhost",
        port=5433,
        dbname="documind",
        user="documind",
        password="localdev",
    )
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM tenants WHERE id = %s", (TEST_TENANT_ID,))
        exists = cur.fetchone() is not None
        if exists:
            print("Test tenant already exists, skipping")
        else:
            cur.execute(
                "INSERT INTO tenants (id, name) VALUES (%s, %s)",
                (TEST_TENANT_ID, "Test Tenant"),
            )
            print("Created test tenant")
    conn.close()


if __name__ == "__main__":
    args = parse_args()
    outputs = get_terraform_outputs(args.env_dir)
    update_env_file(Path(args.env_file), outputs, ENV_TO_TF_OUTPUT)
    bootstrap_test_user(outputs["cognito_user_pool_id"]["value"], "us-east-1")
    ensure_app_role()
    ensure_test_tenant()
    print(json.dumps(outputs, indent=2))
