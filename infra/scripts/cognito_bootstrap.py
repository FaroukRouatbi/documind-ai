import boto3

TEST_TENANT_ID = "11111111-1111-1111-1111-111111111111"


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
        UserAttributes=[{"Name": "custom:tenant_id", "Value": TEST_TENANT_ID}],
    )
    print("Set custom:tenant_id attribute")
