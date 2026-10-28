from collections import Counter
import re
from threading import Lock


_DYNAMIC_PATH = re.compile(r"/[0-9a-fA-F]{8,}(?=/|$)|/[0-9a-fA-F-]{32,}(?=/|$)")


def normalize_path(path: str) -> str:
    """Prevent unbounded metric cardinality from resource and UUID paths."""
    return _DYNAMIC_PATH.sub("/:id", path)


class Metrics:
    def __init__(self) -> None:
        self._lock = Lock()
        self.requests = Counter()
        self.statuses = Counter()
        self.worker = Counter()

    def observe_request(self, method: str, path: str, status_code: int) -> None:
        with self._lock:
            self.requests[f'{method}|{normalize_path(path)}'] += 1
            self.statuses[str(status_code)] += 1

    def observe_worker(self, outcome: str) -> None:
        with self._lock:
            self.worker[outcome] += 1

    def render_prometheus(self) -> str:
        with self._lock:
            lines = ["# HELP roadmap_http_requests_total Total HTTP requests.", "# TYPE roadmap_http_requests_total counter"]
            lines.extend(f'roadmap_http_requests_total{{method="{method}",path="{path}"}} {count}' for (method, path), count in self.requests.items())
            lines.extend(["# HELP roadmap_http_responses_total Total HTTP responses by status code.", "# TYPE roadmap_http_responses_total counter"])
            lines.extend(f'roadmap_http_responses_total{{status="{status}"}} {count}' for status, count in self.statuses.items())
            lines.extend(["# HELP roadmap_document_worker_total Document worker outcomes.", "# TYPE roadmap_document_worker_total counter"])
            lines.extend(f'roadmap_document_worker_total{{outcome="{outcome}"}} {count}' for outcome, count in self.worker.items())
            return "\n".join(lines) + "\n"


metrics = Metrics()
