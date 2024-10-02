from plotly.graph_objects import Figure
from datetime import datetime, timezone, timedelta
from arbiter.models import Violation
from django.conf import settings
from prometheus_api_client import MetricRangeDataFrame
import plotly.express as px

prom = settings.PROMETHEUS_CONNECTION

chart = Figure
pie = Figure

GIB = 1024**3
PROMETHUS_POINT_LIMIT = 400
NSPERSEC = 1_000_000_000
PORT_RE = r"(:[0-9]{1,5})?"


def align_to_step(start: datetime, end: datetime, step:str="15s") -> datetime:
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


def align_with_prom_limit(start: datetime, end: datetime, step:str):
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

def create_usage_figures(
    query: str,
    label: str,
    start: datetime,
    end: datetime,
    threshold: float | None = None,
    penalized: datetime | None = None,
    step: str = "15s",
) -> tuple[chart, pie]:
    start, end = align_to_step(start, end, step)
    result = prom.custom_query_range(query, start_time=start, end_time=end, step=step)

    if not result:
        return None, None

    # create a dataframe from prometheus query, and group all processes under 1%
    df = MetricRangeDataFrame(result)
    df.loc[df.value < 0.01, "proc"] = "other"

    # calculate the average value of a metric
    aggregate = df.groupby(["unit", "instance", "proc"], as_index=False).agg(
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
        line_shape="spline",
        color_discrete_map=color_mapping,
    )
    if threshold:
        chart.add_hline(
            threshold,
            annotation_text="Policy Threshold",
            annotation_position="top left",
            line={"dash": "dot", "color": "grey"},
        )
    if penalized:
        chart.add_vline(
            penalized.timestamp() * 1000,  # convert to ms
            annotation_text="Penalized",
            annotation_position="top left",
            line={"dash": "dash", "color": "grey"},
        )

    return chart, pie


def cpu_usage_figures(
    unit_re: str,
    host_re: str,
    start_time: datetime,
    end_time: datetime,
    policy_threshold: float | None = None,
    penalized_time: datetime | None = None,
    step="15s",
) -> tuple[chart, pie]:
    metric = "systemd_unit_proc_cpu_usage_ns"
    filters = f'{{ unit=~"{ unit_re }", instance=~"{host_re}{PORT_RE}"}}'

    labels = "(unit, instance, proc)"
    query = f"sort_desc(avg by {labels} (rate({metric}{filters}[{step}])) / {NSPERSEC})"
    fig, pie = create_usage_figures(
        query, "proc", start_time, end_time, policy_threshold, penalized_time, step
    )
    fig.update_layout(
        title=f"CPU Usage Report For {unit_re} on {host_re}",
        xaxis_title="Time",
        yaxis_title="Usage in Cores",
    )
    return fig, pie


def mem_usage_figures(
    unit_re: str,
    host_re: str,
    start_time: datetime,
    end_time: datetime,
    policy_threshold: float | None = None,
    penalized_time: datetime | None = None,
    step="15s",
) -> tuple[chart, pie]:
    filters = f'{{ unit=~"{ unit_re }", instance=~"{ host_re }{PORT_RE}"}}'
    metric = "systemd_unit_proc_memory_current_bytes"
    labels = "(unit, instance, proc)"
    query = (
        f"sort_desc(avg by {labels} (avg_over_time({metric}{filters}[{step}])) / {GIB})"
    )
    fig, pie = create_usage_figures(
        query, "proc", start_time, end_time, policy_threshold, penalized_time, step
    )
    fig.update_layout(
        title=f"Memory Usage Report For {unit_re} on {host_re}",
        xaxis_title="Time",
        yaxis_title="Usage in GiB",
    )
    return fig, pie


def violation_cpu_usage_figures(violation: Violation) -> tuple[chart, pie]:
    unit = violation.target.unit
    host = violation.target.host
    start = violation.timestamp - violation.policy.timewindow
    end = violation.expiration
    threshold = violation.policy.query_params.get("cpu_threshold", None)
    penalized = violation.timestamp

    return cpu_usage_figures(unit, host, start, end, threshold, penalized)


def violation_mem_usage_figures(violation: Violation) -> tuple[chart, pie]:
    unit = violation.target.unit
    host = violation.target.host
    start = violation.timestamp - violation.policy.timewindow
    end = violation.expiration
    threshold = violation.policy.query_params.get("memory_threshold", None)
    penalized = violation.timestamp

    return mem_usage_figures(unit, host, start, end, threshold, penalized)
