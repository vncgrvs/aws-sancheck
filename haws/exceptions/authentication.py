class UnauthenticatedUserCredentials(Exception):
    pass


class FailedPolicyCheck(Exception):
    pass


class InvalidUserCredentials(Exception):
    pass


class GeneralAuthError(Exception):
    pass


class NoRuntimeSettings(Exception):
    pass


class MultipleRoots(Exception):
    pass


class AccessDenied(Exception):
    pass
