import argparse
import json
import subprocess
import boto3
from pathlib import Path


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

def bootstrap_test_user(pool_id: str, region: str) -> None:
    client = boto3.client("cognito-idp", region_name=region)

    try:
        client.admin_create_user(
            UserPoolId=pool_id,
            Username="testuser@example.com",
            UserAttributes=[
                {"Name": "email", "Value": "testuser@example.com"},
                {"Name": "email_verified", "Value": "true"},
            ],
            TemporaryPassword="TempPass123!",
            MessageAction="SUPPRESS",
        )
        print("Created test user")
    except client.exceptions.UsernameExistsException:
        print("Test user already exists, skipping creation")

    client.admin_set_user_password(
        UserPoolId=pool_id,
        Username="testuser@example.com",
        Password="RealPass123!",
        Permanent=True,
    )

    client.admin_update_user_attributes(
        UserPoolId=pool_id,
        Username="testuser@example.com",
        UserAttributes=[{"Name": "custom:tenant_id", "Value": "test-tenant-123"}],
    )
    print("Set custom:tenant_id attribute")

if __name__ == "__main__":
    args = parse_args()
    outputs = get_terraform_outputs(args.env_dir)
    update_env_file(Path(args.env_file), outputs, ENV_TO_TF_OUTPUT)
    bootstrap_test_user(outputs["cognito_user_pool_id"]["value"], "us-east-1")
    print(json.dumps(outputs, indent=2))
