import logging
from typing import NamedTuple
from datetime import datetime, timedelta, timezone

from plotly.graph_objects import Figure
from prometheus_api_client import MetricRangeDataFrame, PrometheusApiClientException
import plotly.express as px

from django.utils.timezone import get_current_timezone, localtime

from arbiter.models import Violation
from arbiter.utils import bytes_to_gib, BYTES_PER_GIB, log_debug
from arbiter.conf import PROMETHEUS_CONNECTION


logger = logging.getLogger(__name__)


PROMETHUS_POINT_LIMIT = 400
PORT_RE = r"(:[0-9]{1,5})?"

MEM_USAGE = "mem"
CPU_USAGE = "cpu"


class Figures(NamedTuple):
    chart : Figure
    pie   : Figure


def _align_to_step(start: datetime, end: datetime, step: str = "15s") -> datetime:
    """
    Given a duration as defined by the start and end, ensure the duration is
    aligned to the given step size.
    """

    start_seconds = int(start.astimezone(timezone.utc).timestamp())
    end_seconds = int(start.astimezone(timezone.utc).timestamp())

    if step[-1] == "s":
        step_seconds = int(step[:-1])
    elif step[-1] == "m":
        step_seconds = int(step[:-1]) * 60

    start_delta = timedelta(seconds=(start_seconds % step_seconds))
    end_delta = timedelta(seconds=(end_seconds % step_seconds))

    return start - start_delta, end - end_delta


def _align_with_prom_limit(start: datetime, end: datetime, step: str) -> str:
    """
    Given a timerange as defined by the start and end, create a step
    interval for a prometheus query that ensures no more than 400
    results will be returned.
    """

    total_range_seconds = (end - start).total_seconds()

    if step[-1] == "s":
        step_seconds = int(step[:-1])
    elif step[-1] == "m":
        step_seconds = int(step[:-1]) * 60

    if total_range_seconds / step_seconds >= 400:
        return f"{int(total_range_seconds // 400)}s"
    else:
        return step


def _usage_figures(
    query: str,
    label: str,
    start: datetime,
    end: datetime,
    threshold: float | None = None,
    step: str = "30s",
) -> Figures | None:

    start, end = _align_to_step(start, end, step)

    try:
        result = PROMETHEUS_CONNECTION.custom_query_range(query, start_time=start, end_time=end, step=step)
    except PrometheusApiClientException as e:
        logger.error(f'unable to create usage figures: {e}')
        logger.info(f'query: {query}')
        return None

    if not result:
        logger.warning(f"unable to create usage figures: empty query result")
        logger.info(f'query: {query}')
        return None

    local_tz = get_current_timezone()

    # convert start and end (utc) to local
    start = localtime(start)
    end = localtime(end)

    # create a dataframe from prometheus query
    df = MetricRangeDataFrame(result)

    # convert timestamps (utc) to local
    df.index = df.index.tz_localize("UTC").tz_convert(local_tz)

    # group all processes under 1%
    df.loc[df.value < 0.01, "proc"] = "other"

    # calculate the average value of a metric
    aggregate = df.groupby(["username", "instance", "proc"], as_index=False).agg(
        mean=("value", "mean")
    )
    aggregate["pct"] = aggregate["mean"] / aggregate["mean"].sum()
    aggregate.loc[aggregate.pct < 0.01, "proc"] = "other"

    # assign pretty colors to unique processes
    proc_list = aggregate["proc"].unique()
    color_mapping = dict()
    color_cursor = 0
    swatch = px.colors.qualitative.Light24
    for proc in proc_list:
        color_mapping[proc] = swatch[color_cursor % len(swatch)]
        color_cursor += 1

    # create a pie chart with process usage averages
    pie = px.pie(
        aggregate,
        values="pct",
        names="proc",
        color=label,
        labels={"proc": "process", "mean": "value"},
        color_discrete_map=color_mapping,
        opacity=0.75,
    )
    pie.update_traces(textposition="inside", textinfo="percent+label")
    pie.layout.showlegend = False

    df.loc[~df["proc"].isin(proc_list), "proc"] = "other"
    chart = px.area(
        df.sort_values(by=["value"]),
        y="value",
        color=label,
        line_shape="hv",
        color_discrete_map=color_mapping,
    )

    # remove lines, only have area
    for i in range(len(chart['data'])):
        chart['data'][i]['line']['width'] = 0


    # if there is a threshold to graph
    if threshold:
        chart.add_hline(
            threshold,
            line={"dash": "dot", "color": "grey"},
        )

    return Figures(chart=chart, pie=pie)

@log_debug
def violation_usage_figures(violation: Violation, usage_type: str, step: str = "30s") -> Figures | None:
    username = violation.target.username
    host = violation.target.host
    start = violation.timestamp - violation.policy.lookback
    end = violation.timestamp
    step = _align_with_prom_limit(start, end, step)

    if usage_type == CPU_USAGE:
        threshold = violation.policy.cpu_threshold or None
        return cpu_usage_figures(username, host, start, end, threshold, step)

    if usage_type == MEM_USAGE:
        if threshold := violation.policy.mem_threshold or None:
            threshold = bytes_to_gib(threshold)
        return mem_usage_figures(username, host, start, end, threshold, step)

    return None


def violation_cpu_usage_figures(violation: Violation, step: str = "30s") -> Figures | None: 
    return violation_usage_figures(violation, CPU_USAGE, step)


def violation_mem_usage_figures(violation: Violation, step: str = "30s") -> Figures | None:
    return violation_usage_figures(violation, MEM_USAGE, step)


def cpu_usage_figures(
    username_re: str,
    host_re: str,
    start_time: datetime,
    end_time: datetime,
    policy_threshold: float | None = None,
    step="30s",
) -> Figures | None:
    
    unit_total = f'sum by (username, instance) (rate(cgroup_warden_cpu_usage_seconds{{username="{username_re}", instance=~"{host_re}{PORT_RE}"}}[{step}]))'
    proc_total = f'sum by (username, instance) (rate(cgroup_warden_proc_cpu_usage_seconds{{username="{username_re}", instance=~"{host_re}{PORT_RE}"}}[{step}]))'
    proc_delta = f'label_replace({unit_total} - {proc_total}, "proc", "unknown", "proc", "") > 0'
    query = f'{proc_delta} or sum by (username, instance, proc) (rate(cgroup_warden_proc_cpu_usage_seconds{{username="{username_re}", instance=~"{host_re}{PORT_RE}"}}[{step}]))'

    figures = _usage_figures(
        query,
        "proc",
        start_time,
        end_time,
        policy_threshold,
        step,
    )

    if not figures:
        return None

    figures.chart.update_layout(
        title=f"CPU Usage Report For {username_re} on {host_re}",
        xaxis_title="Time",
        yaxis_title="Usage in Cores",
    )
    return figures


def mem_usage_figures(
    username_re: str,
    host_re: str,
    start_time: datetime,
    end_time: datetime,
    policy_threshold: float | None = None,
    step="30s",
) -> Figures | None:
    
    unit_total = f'sum by (username, instance) (cgroup_warden_memory_usage_bytes{{username="{username_re}", instance=~"{host_re}{PORT_RE}"}} / {BYTES_PER_GIB})'
    proc_total = f'sum by (username, instance) (cgroup_warden_proc_memory_usage_bytes{{username="{username_re}", instance=~"{host_re}{PORT_RE}"}} / {BYTES_PER_GIB})'
    proc_delta = f'label_replace({unit_total} - {proc_total}, "proc", "unknown", "proc", "") > 0'
    query = f'{proc_delta} or sum by (username, instance, proc) (cgroup_warden_proc_memory_usage_bytes{{username="{username_re}", instance=~"{host_re}{PORT_RE}"}} / {BYTES_PER_GIB})'

    figures = _usage_figures(
        query,
        "proc",
        start_time,
        end_time,
        policy_threshold,
        step,
    )

    if not figures:
        return None

    figures.chart.update_layout(
        title=f"Memory Usage Report For {username_re} on {host_re}",
        xaxis_title="Time",
        yaxis_title="Usage in GiB",
    )
    return figures
