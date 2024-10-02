from plotly.graph_objects import Figure
from datetime import datetime, timezone as tz
from django.utils import timezone
from zoneinfo import ZoneInfo
from arbiter.models import Violation
from django.conf import settings
from prometheus_api_client import MetricRangeDataFrame, MetricSnapshotDataFrame
import plotly.express as px

prom = settings.PROMETHEUS_CONNECTION

GIB = 1024**3
PROMETHUS_POINT_LIMIT = 400
NSPERSEC = 1_000_000_000
PORT_RE = r'(:[0-9]{1,5})?'

def align_to_step(start_time: datetime, end_time: datetime, step = "15s") -> datetime:
    end_time_seconds = int(end_time.timestamp())
    start_time_seconds = int(start_time.timestamp())
    
    if step[-1] == "s":
        step_seconds = int(step[:-1])
    elif step[-1] == "m":
        step_seconds = int(step[:-1]) * 60

    end_time_seconds = end_time_seconds - (end_time_seconds % step_seconds)
    start_time_seconds = start_time_seconds - (start_time_seconds % step_seconds)

    end_time = timezone.make_aware(datetime.fromtimestamp(end_time_seconds))
    start_time = timezone.make_aware(datetime.fromtimestamp(start_time_seconds))
    return start_time, end_time
    

def align_with_prom_limit(start_time, end_time, step):
    total_range_seconds = (end_time - start_time).total_seconds()

    if step[-1] == "s":
        step_seconds = int(step[:-1])
    elif step[-1] == "m":
        step_seconds = int(step[:-1]) * 60

    if total_range_seconds / step_seconds >= 400:
        return f"{int(total_range_seconds // 400)}s"
    else:
        return step


def usage_graph(query: str, label: str, start: datetime, end: datetime, threshold: float | None = None, penalized: datetime | None = None, step: str = "15s"):
    start, end = align_to_step(start, end, step)
    result = prom.custom_query_range(query, start_time=start, end_time=end, step=step)

    if not result:
        return Figure()

    df = MetricRangeDataFrame(result)
    df.loc[df.value < 0.01, 'proc'] = 'other'
    
    fig = px.area(df.sort_values(by=['value']), y="value", color=label, line_shape='spline', color_discrete_sequence=px.colors.qualitative.Light24)
    if threshold:
        fig.add_hline(
            threshold,
            annotation_text="Policy Threshold",
            annotation_position="top left",
            line={"dash": "dot", "color": "grey"},
        )
    if penalized:
        fig.add_vline(
            penalized.timestamp() * 1000, # convert to ms
            annotation_text="Penalized",
            annotation_position="top left",
            line={"dash": "dash", "color": "grey"},
        )
    return fig


def cpu_usage_graph(
    unit_re: str,
    host_re: str,
    start_time: datetime,
    end_time: datetime,
    policy_threshold: float | None = None,
    penalized_time: datetime | None = None,
    step="15s",
) -> tuple[Figure, Figure]:
    
    metric = 'systemd_unit_proc_cpu_usage_ns'
    filters = f'{{ unit=~"{ unit_re }", instance=~"{host_re}{PORT_RE}"}}'
   
    labels = "(unit, instance, proc)"
    query = f'sort_desc(avg by {labels} (rate({metric}{filters}[{step}])) / {NSPERSEC})'
    fig, pie = usage_charts(query, "proc", start_time, end_time, policy_threshold, penalized_time, step)   
    fig.update_layout(
        title=f"CPU Usage Report For {unit_re} on {host_re}",
        xaxis_title="Time",
        yaxis_title="Usage in Cores",
    )
    return fig, pie

def usage_charts(query: str, label: str, start: datetime, end: datetime, threshold: float | None = None, penalized: datetime | None = None, step: str = "15s") -> tuple[Figure]:
    start, end = align_to_step(start, end, step)
    result = prom.custom_query_range(query, start_time=start, end_time=end, step=step)

    if not result:
        return Figure(), Figure()

    df = MetricRangeDataFrame(result)
    df.loc[df.value < 0.01, 'proc'] = 'other'

    aggregate = df.groupby(['unit','instance', 'proc'], as_index=False).agg(mean=('value','mean'))
    aggregate['pct'] = (aggregate['mean'] / aggregate['mean'].sum())
    aggregate.loc[aggregate.pct < 0.01, 'proc'] = 'other'

    proc_list = aggregate['proc'].unique()
    color_mapping =  dict()
    color_cursor = 0
    swatch = px.colors.qualitative.Light24
    for proc in proc_list:
        color_mapping[proc] = swatch[color_cursor%len(swatch)]
        color_cursor += 1
        
    pie = px.pie(aggregate, values="pct", names="proc", color=label, labels={'proc':'process', 'mean': "value"}, color_discrete_map=color_mapping, opacity=0.75)
    pie.update_traces(textposition='inside', textinfo='percent+label')
    pie.layout.showlegend = False
    

    df.loc[~df['proc'].isin(proc_list), 'proc'] = 'other'
    graph = px.area(df.sort_values(by=['value']), y="value", color=label, line_shape='spline', color_discrete_map=color_mapping)
    if threshold:
        graph.add_hline(
            threshold,
            annotation_text="Policy Threshold",
            annotation_position="top left",
            line={"dash": "dot", "color": "grey"},
        )
    if penalized:
        graph.add_vline(
            penalized.timestamp() * 1000, # convert to ms
            annotation_text="Penalized",
            annotation_position="top left",
            line={"dash": "dash", "color": "grey"},
        )
    
    

    return graph, pie


def mem_usage_graph(
    unit_re: str,
    host_re: str,
    start_time: datetime,
    end_time: datetime,
    policy_threshold: float | None = None,
    penalized_time: datetime | None = None,
    step="10s",
) -> tuple[Figure, Figure]:
    filters = f'{{ unit=~"{ unit_re }", instance=~"{ host_re }{PORT_RE}"}}'
    metric = 'systemd_unit_proc_memory_current_bytes'
    labels = "(unit, instance, proc)"
    query = f"sort_desc(avg by {labels} (avg_over_time({metric}{filters}[{step}])) / {GIB})"
    fig, pie = usage_charts(query, "proc", start_time, end_time, policy_threshold, penalized_time, step)   
    fig.update_layout(
        title=f"Memory Usage Report For {unit_re} on {host_re}",
        xaxis_title="Time",
        yaxis_title="Usage in GiB",
    )
    return fig, pie


def instant_response_to_data(response: dict, group_label: str, unit_divisor=1) -> dict:
    pie_data = dict()

    for metric in response:
        current_label = metric["metric"][group_label]

        pie_data[current_label] = float(metric["value"][1]) / unit_divisor

    return pie_data

def pie_graph(
    query: str,
    start: datetime,
    end: datetime,
    step="15s"
):
    start, end = align_to_step(start, end, step)
    result = prom.custom_query_range(query, start_time=start, end_time=end, step=step)

    if not result:
        return Figure()

    df = MetricRangeDataFrame(result)
    df = df[df.value != 0]
    aggregate = df.groupby(['unit','instance', 'proc'], as_index=False).agg(mean=('value','mean'))
    aggregate['pct'] = (aggregate['mean'] / aggregate['mean'].sum())
    aggregate.loc[aggregate.pct < 0.01, 'proc'] = 'other'
    fig = px.pie(aggregate, values="mean", names="proc",labels={'proc':'process', 'mean': "value"})
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.layout.showlegend = False
    return fig

def cpu_pie_graph(
    unit_re: str, host_re: str, start_time: datetime, end_time: datetime
) -> Figure:
    filters = f'{{ unit=~"{ unit_re }", instance=~"{ host_re }{PORT_RE}"}}'
    metric = 'systemd_unit_proc_cpu_usage_ns'
    labels = "(unit, instance, proc)"
    time = int((end_time - start_time).total_seconds())
    query = f"sum by {labels}(rate({metric}{filters}[{time}s]))/ {NSPERSEC}"
    fig = pie_graph(query, start_time, end_time)   
    fig.update_layout(
        title=f" % CPU Usage Report For {unit_re} on {host_re}",
        xaxis_title="Time",
        yaxis_title="Usage in cores",
    )
    return fig


def mem_pie_graph(
    unit_re: str, host_re: str, start_time: datetime, end_time: datetime
) -> Figure:
    filters = f'{{ unit=~"{ unit_re }", instance=~"{ host_re }{PORT_RE}"}}'
    metric = 'systemd_unit_proc_memory_current_bytes'
    labels = "(unit, instance, proc)"
    time = int((end_time - start_time).total_seconds())
    query = f"avg by {labels}(avg_over_time({metric}{filters}[{time}s]) / {GIB})"
    fig = pie_graph(query, start_time, end_time)   
    fig.update_layout(
        title=f"% Memory Usage Report For {unit_re} on {host_re}",
        xaxis_title="Time",
        yaxis_title="Usage in GiB",
    )
    return fig

def plot_violation_cpu_graph(violation: Violation, step="10s") -> Figure:
    start_time = violation.timestamp - violation.policy.timewindow
    end_time = violation.expiration
    step = align_with_prom_limit(start_time, end_time, step)

    return cpu_usage_graph(
        violation.target.unit,
        violation.target.host,
        start_time=start_time.astimezone,
        end_time=end_time.astimezone(tz.utc),
        policy_threshold=violation.policy.query_params.get("cpu_threshold", None),
        penalized_time=violation.timestamp.astimezone(ZoneInfo("UTC")),
        step=step,
    )


def plot_violation_memory_graph(violation: Violation, step="10s") -> Figure:
    start_time = violation.timestamp - violation.policy.timewindow
    end_time = violation.expiration
    step = align_with_prom_limit(start_time, end_time, step)

    return mem_usage_graph(
        violation.target.unit,
        violation.target.host,
        start_time=start_time.astimezone(tz.utc),
        end_time=end_time.astimezone(tz.utc),
        policy_threshold=violation.policy.query_params.get("memory_threshold", None),
        penalized_time=violation.timestamp.astimezone(ZoneInfo("UTC")),
        step=step,
    )


def plot_violation_proc_cpu_usage_pie(violation: Violation) -> Figure:
    start_time = violation.timestamp - violation.policy.timewindow
    end_time = violation.timestamp

    return cpu_pie_graph(
        violation.target.unit,
        violation.target.host,
        start_time=start_time,
        end_time=end_time,
    )


def plot_violation_proc_memory_usage_pie(violation: Violation) -> Figure:
    start_time = violation.timestamp - violation.policy.timewindow
    end_time = violation.timestamp

    return mem_pie_graph(
        violation.target.unit,
        violation.target.host,
        start_time=start_time,
        end_time=end_time,
    )
