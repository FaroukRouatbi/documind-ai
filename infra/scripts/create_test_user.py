import subprocess

from cognito_bootstrap import bootstrap_test_user


def get_pool_id(env_dir: str) -> str:
    result = subprocess.run(
        ["terraform", f"-chdir={env_dir}", "output", "-raw", "cognito_user_pool_id"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


import argparse


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-dir", default="../environments/dev")
    parser.add_argument("--region", default="us-east-1")
    args = parser.parse_args()

    pool_id = get_pool_id(args.env_dir)
    print(f"Bootstrapping test user in pool {pool_id}")
    bootstrap_test_user(pool_id, args.region)


if __name__ == "__main__":
    main()
