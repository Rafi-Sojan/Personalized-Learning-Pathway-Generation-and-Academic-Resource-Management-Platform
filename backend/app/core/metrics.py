from collections import Counter
from threading import Lock


class Metrics:
    def __init__(self) -> None:
        self._lock = Lock()
        self.requests = Counter()
        self.statuses = Counter()

    def observe_request(self, method: str, path: str, status_code: int) -> None:
        with self._lock:
            self.requests[f'{method}|{path}'] += 1
            self.statuses[str(status_code)] += 1

    def render_prometheus(self) -> str:
        with self._lock:
            lines = ["# HELP roadmap_http_requests_total Total HTTP requests.", "# TYPE roadmap_http_requests_total counter"]
            lines.extend(f'roadmap_http_requests_total{{method="{method}",path="{path}"}} {count}' for (method, path), count in self.requests.items())
            lines.extend(["# HELP roadmap_http_responses_total Total HTTP responses by status code.", "# TYPE roadmap_http_responses_total counter"])
            lines.extend(f'roadmap_http_responses_total{{status="{status}"}} {count}' for status, count in self.statuses.items())
            return "\n".join(lines) + "\n"


metrics = Metrics()
