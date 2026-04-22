"""
Custom DRF exception handler to enforce a unified error format.
"""

from rest_framework.response import Response
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    """
    Return errors in a consistent envelope:
    { "error": { "type": "<ExceptionClass>", "detail": "...", "status": 400 } }
    """
    response = exception_handler(exc, context)
    if response is None:
        return response

    data = response.data
    detail = data
    if isinstance(data, dict) and "detail" in data:
        detail = data["detail"]
    error_payload = {
        "error": {
            "type": exc.__class__.__name__,
            "detail": detail,
            "status": response.status_code,
        }
    }
    return Response(error_payload, status=response.status_code)
