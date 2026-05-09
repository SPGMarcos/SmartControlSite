import logging
from contextvars import ContextVar


request_id_context = ContextVar("request_id", default="-")


class RequestIdLogFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id_context.get()
        return True
