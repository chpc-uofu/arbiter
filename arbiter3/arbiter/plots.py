import logging
from datetime import datetime, timedelta, timezone
import re

from plotly.graph_objects import Figure, Scatter

from django.utils.timezone import get_current_timezone, localtime

from arbiter3.arbiter.models import Violation
from arbiter3.arbiter.utils import bytes_to_gib, BYTES_PER_GIB
from arbiter3.arbiter.conf import PROMETHEUS_CONNECTION
from arbiter3.arbiter.promclient import sort_matrices_by_avg, combine_last_matrices, Matrix
from arbiter3.arbiter.query import Q, rate, sum_by, max_over_time, avg_over_time

logger = logging.getLogger(__name__)


class QueryError(Exception):
    pass


def _usage_graph_data(
        query: str, 
        start: datetime, 
        end: datetime, 
        step: str, 
    ) -> list[Matrix]:

    try:
        matrices = PROMETHEUS_CONNECTION.query_range(query=query, start=start.timestamp(), end=end.timestamp(), step=step)
    except Exception as e:
        raise QueryError(f'Could not run query: {e}')

    if not matrices:
        raise QueryError(f"Query returned no results: {query}")

    matrices = sort_matrices_by_avg(matrices)

    return matrices


def _graph_from_matrices(matrices: list[Matrix], color_by: str, threshold: float | int | None, whitelist: str | None = None, counts : dict| None = None) -> Figure:
    fig = Figure()

    for result_matrix in reversed(matrices):
        timestamps = [datetime.fromtimestamp(point.timestamp) for point in result_matrix.values]
        values = [float(point.value) for point in result_matrix.values]
        
        name = result_matrix.metric[color_by]
        display_name = name


        if whitelist and re.match(whitelist, name):
            display_name += "*"
         
        if counts and (name_count := counts.get(name)):
            display_name += f' ({name_count})'

        fig.add_trace(
            Scatter(
                x=timestamps, 
                y=values,
                hoverinfo="name+x+y",
                mode='lines',
                line=dict(width=0.0),
                stackgroup='main',
                name=display_name
            ),
        ) 
        
    if threshold:
        fig.add_hline(threshold, line={"dash": "dot", "color": "grey"})

    return fig


def proc_usage_graph(
        query: Q, 
        start: datetime, 
        end: datetime, 
        step: str, 
        threshold: float | int | None, 
        whitelist: str | None = None,
        unreported_query: Q = None,
    ) -> Figure:

    matrices = _usage_graph_data(str(query), start, end, step)
    
    if unreported_query:
        try:
            unreported_matrix = PROMETHEUS_CONNECTION.query_range(query=str(unreported_query), start=start.timestamp(), end=end.timestamp(), step=step)
        except Exception as e:
            raise QueryError(f'Could not run unreported query: {e}')
        
        #extend process list to include unreported usage
        if unreported_matrix:
            matrices.extend(unreported_matrix)

    # show top 7 procs (if statement is to ensure unreported goes to 'other' label)
    matrices = combine_last_matrices(matrices, 7 if len(matrices) > 7 else len(matrices) - 1)

    window = f'{int((end - start ).total_seconds())}s'
    
    try:
        proc_counts_query = max_over_time(Q('cgroup_warden_proc_count').over(window))
        proc_counts_query._matchers = query._matchers

        proc_counts = {result.metric['proc']: int(result.value.value) for result in PROMETHEUS_CONNECTION.query(query=str(proc_counts_query))}
    except Exception as e:
        raise QueryError(f'Could not run unreported query: {e}')
    
    fig = _graph_from_matrices(
        matrices,
        color_by='proc',
        threshold=threshold,
        whitelist=whitelist,
        counts=proc_counts,
    )
    
    return fig

def user_usage_graph(
        query: Q, 
        start: datetime, 
        end: datetime, 
        step: str, 
        threshold: float | int | None, 
        whitelist: str | None = None,
    ) -> Figure:

    matrices = _usage_graph_data(str(query), start, end, step)
    
    fig = _graph_from_matrices(
        matrices,
        color_by='username',
        threshold=threshold,
        whitelist=whitelist,
    )
    
    return fig


def cpu_usage_figure(host: str, start: datetime, end: datetime, step="30s", username: str = None, threshold: float = None, whitelist: str = None) -> Figure | None:
    if username:
        query = rate(Q('cgroup_warden_proc_cpu_usage_seconds').matches(instance=host, username=username).over(step))
        unreported_query = (sum_by(rate(Q('cgroup_warden_cpu_usage_seconds').matches(instance=host, username=username).over(step))) - sum_by(query.copy())) > 0
        figure = proc_usage_graph(query, start, end, step, threshold, whitelist, unreported_query)
    else:
        query = rate(Q('cgroup_warden_cpu_usage_seconds').matches(instance=host).over(step))
        figure = user_usage_graph(query, start, end, step, threshold, whitelist)

    title = f"CPU usage for {username} on {host}" if username else f"CPU usage on {host}"
    figure.update_layout(title=title, yaxis_title="Cores")
    
    return figure


def mem_usage_figure(host: str, start: datetime, end: datetime, step="30s", username: str = None, threshold: int = None, whitelist: str = None) -> Figure | None:
    if username:
        query = avg_over_time(Q('cgroup_warden_proc_memory_pss_bytes').matches(instance=host, username=username).over(step)) 
        unreported_query = ((sum_by(avg_over_time(Q('cgroup_warden_memory_usage_bytes').matches(instance=host, username=username).over(step))) - sum_by(query.copy())) / BYTES_PER_GIB) > 0
        query = query / BYTES_PER_GIB

        figure = proc_usage_graph(query, start, end, step, threshold, whitelist, unreported_query)
    else:
        query = Q('cgroup_warden_memory_usage_bytes').matches(instance=host)/ BYTES_PER_GIB
        figure = user_usage_graph(query, start, end, step, threshold, whitelist)

    title = f"Memory usage for {username} on {host}" if username else f"Memory usage on {host}"
    figure.update_layout(title=title, yaxis_title="GiB")
    return figure


def violation_cpu_usage_figure(violation: Violation, step: str = "1m") -> Figure | None:
    username = violation.target.username
    host = violation.target.instance
    start = violation.timestamp - violation.policy.lookback
    end = violation.timestamp
    step = align_with_prom_limit(start, end, step)


    figure = cpu_usage_figure(
        host=host,
        start=start,
        end=end, 
        step=step, 
        username=username,
        threshold=violation.policy.cpu_threshold,
        whitelist=violation.policy.proc_whitelist,
    )

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

    figure = mem_usage_figure(
        host=host,
        start=start,
        end=end, 
        step=step, 
        username=username,
        threshold=threshold,
        whitelist=violation.policy.proc_whitelist,
    )

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
