class SingularClientException(BaseException):
    pass


class ArgumentValidationException(SingularClientException):
    pass


class APIException(SingularClientException):
    pass
