class SingularClientException(Exception):
    pass


class ArgumentValidationException(SingularClientException):
    """
    An expected Argument Validation Exception (retrying won't help)
    """
    pass


class APIException(SingularClientException):
    """
    An expected API exception (retrying won't help)
    """
    pass


class UnexpectedAPIException(SingularClientException):
    """
    Unexpected Singular API error (consider retrying in a few moments)
    """
    pass


def retry_if_unexpected_error(exception):
    return isinstance(exception, UnexpectedAPIException)
