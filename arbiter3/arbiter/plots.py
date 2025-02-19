import logging
from datetime import datetime, timedelta, timezone

from plotly.graph_objects import Figure
from prometheus_api_client import MetricRangeDataFrame, PrometheusApiClientException
import plotly.express as px

from django.utils.timezone import get_current_timezone, localtime

from arbiter3.arbiter.models import Violation
from arbiter3.arbiter.utils import bytes_to_gib, BYTES_PER_GIB
from arbiter3.arbiter.conf import PROMETHEUS_CONNECTION

logger = logging.getLogger(__name__)


class QueryError(Exception):
    pass


def usage_graph(query: str, start: datetime, end: datetime, step: str, color_by: str, threshold: float | int | None) -> Figure:

    try:
        result = PROMETHEUS_CONNECTION.custom_query_range(
            query, start_time=start, end_time=end, step=step)
    except PrometheusApiClientException as e:
        raise QueryError(f"Could not run query: {e}")

    if not result:
        raise QueryError(
            f"Query returned no results: {query}. Try increasing step size.")

    start, end = time_aligned_and_local(start, end, step)
    df = MetricRangeDataFrame(result)
    df.index = df.index.tz_localize("UTC").tz_convert(get_current_timezone())
    sort_by = ["value", color_by] if color_by == "proc" else ["value"]
    df = df.sort_values(by=sort_by)

    graph = px.area(df, y="value", line_shape="hv", color=color_by)
    graph.update_layout(xaxis_title="")

    for i in range(len(graph['data'])):
        graph['data'][i]['line']['width'] = 0

    if threshold:
        graph.add_hline(threshold, line={"dash": "dot", "color": "grey"})

    return graph


def cpu_usage_figure(host: str, start: datetime, end: datetime, step="30s", username: str = None, threshold: float = None) -> Figure | None:
    if username:
        query = f'rate(cgroup_warden_proc_cpu_usage_seconds{{instance="{host}", username="{username}"}}[{step}])'
        color_by = "proc"
    else:
        query = f'rate(cgroup_warden_cpu_usage_seconds{{instance="{host}"}}[{step}])'
        color_by = "username"

    figure = usage_graph(query, start, end, step, color_by, threshold)
    title = f"CPU usage for {username} on {host}" if username else f"CPU usage on {host}"
    figure.update_layout(title=title, yaxis_title="Cores")
    return figure


def mem_usage_figure(host: str, start: datetime, end: datetime, step="30s", username: str = None, threshold: int = None) -> Figure | None:
    if username:
        query = f'cgroup_warden_proc_memory_usage_bytes{{instance="{host}", username="{username}"}} / {BYTES_PER_GIB}'
        color_by = "proc"
    else:
        query = f'cgroup_warden_memory_usage_bytes{{instance="{host}"}} / {BYTES_PER_GIB}'
        color_by = "username"

    figure = usage_graph(query, start, end, step, color_by, threshold)
    title = f"Memory usage for {username} on {host}" if username else f"Memory usage on {host}"
    figure.update_layout(title=title, yaxis_title="GiB")
    return figure


def violation_cpu_usage_figure(violation: Violation, step: str = "1m") -> Figure | None:
    username = violation.target.username
    host = violation.target.instance
    start = violation.timestamp - violation.policy.lookback
    end = violation.timestamp
    step = align_with_prom_limit(start, end, step)
    threshold = violation.policy.cpu_threshold
    figure = cpu_usage_figure(host, start, end, step, username, threshold)
    title = f"CPU usage for {username} on {host}"
    figure.update_layout(title=title, yaxis_title="Cores")
    return figure


def violation_mem_usage_figure(violation: Violation, step: str = "1m") -> Figure | None:
    username = violation.target.username
    host = violation.target.instance
    start = violation.timestamp - violation.policy.lookback
    end = violation.timestamp
    step = align_with_prom_limit(start, end, step)
    if threshold := violation.policy.mem_threshold:
        threshold = bytes_to_gib(threshold)
    figure = mem_usage_figure(host, start, end, step, username, threshold)
    title = f"Memory usage for {username} on {host}"
    figure.update_layout(title=title, yaxis_title="GiB")
    return figure


def time_aligned_and_local(start: datetime, end: datetime, step: datetime) -> tuple[datetime, datetime]:
    start, end = align_to_step(start, end, step)
    local_tz = get_current_timezone()
    return localtime(start, local_tz), localtime(end, local_tz)


def align_to_step(start: datetime, end: datetime, step: str = "15s") -> tuple[datetime, datetime]:
    start_seconds = int(start.astimezone(timezone.utc).timestamp())
    end_seconds = int(start.astimezone(timezone.utc).timestamp())

    if step[-1] == "s":
        step_seconds = int(step[:-1])
    elif step[-1] == "m":
        step_seconds = int(step[:-1]) * 60

    start_delta = timedelta(seconds=(start_seconds % step_seconds))
    end_delta = timedelta(seconds=(end_seconds % step_seconds))

    return start - start_delta, end - end_delta


def align_with_prom_limit(start: datetime, end: datetime, step: str) -> str:
    total_range_seconds = (end - start).total_seconds()

    if step[-1] == "s":
        step_seconds = int(step[:-1])
    elif step[-1] == "m":
        step_seconds = int(step[:-1]) * 60

    if total_range_seconds / step_seconds >= 400:
        return f"{int(total_range_seconds // 400)}s"
    else:
        return step
