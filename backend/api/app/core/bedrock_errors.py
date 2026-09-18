from botocore.exceptions import ClientError

TRANSIENT_ERROR_CODES = {
    "ThrottlingException",
    "ServiceUnavailableException",
    "ModelTimeoutException",
    "InternalServerException",
    "ModelNotReadyException",
}


def is_transient(exc: Exception) -> bool:
    if isinstance(exc, ClientError):
        return exc.response["Error"]["Code"] in TRANSIENT_ERROR_CODES
    return False


def is_permanent(exc: Exception) -> bool:
    return not is_transient(exc)
