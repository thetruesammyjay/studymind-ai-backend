class AppError(Exception):
    """Base error class for application."""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class NotFoundError(AppError):
    def __init__(self, resource: str):
        super().__init__(f"{resource} not found", status_code=404)

class ValidationError(AppError):
    def __init__(self, message: str):
        super().__init__(message, status_code=422)

class AuthenticationError(AppError):
    def __init__(self, message: str = "Not authenticated"):
        super().__init__(message, status_code=401)

class AuthorizationError(AppError):
    def __init__(self, message: str = "Not authorized"):
        super().__init__(message, status_code=403)
