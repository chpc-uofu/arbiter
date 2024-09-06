from plotly.graph_objects import Scatter, Figure, Pie
from datetime import datetime
from zoneinfo import ZoneInfo
from arbiter.models import Violation
from django.conf import settings

prom = settings.PROMETHEUS_CONNECTION

# TODO:
# host user usage graphs
# make sure the plotlyjs JS libraries are in the base admin template
GIB = 1024**3

PROMETHUS_POINT_LIMIT = 400


def align_with_prom_limit(start_time, end_time, step):
    """
    Returns the aligned step size (unchanged if it was valid)
    """
    total_range_seconds = (end_time - start_time).total_seconds()

    if step[-1] == "s":
        step_seconds = int(step[:-1])
    elif step[-1] == "m":
        step_seconds = int(step[:-1]) * 60

    if total_range_seconds / step_seconds >= 400:
        return f"{int(total_range_seconds // 400)}s"
    else:
        return step


def response_to_graph_data(
    response: list, group_label: str = None, unit_divisor=1, omit_negative=False
) -> dict:
    """
    Converts from a prometheus response into a more plotly friendly dictionary, where the key is the label we split responses by
    and the Value is a dictionary with the keys "times" and "values" for the respective x, y in plotly.

    Args:
    - response - the response from the prometheus api
    - group_label - the label the response values are grouped by
    - unit_divisor - what to divide the response values by (if unit conversions are needed)
    - omit_negative - if you want gaps in your graph when the value is -1, set to true
    """

    graph_data = dict()
    # Omit negative has its own loop because we need to enter blank values for gaps but we dont want to check omit_negative every loop cycle
    if omit_negative:
        for metric in response:
            current_label = metric["metric"][group_label] if group_label else "other"
            times = []
            values = []
            for point in metric["values"]:
                if float(point[1]) != -1:
                    times.append(
                        datetime.fromtimestamp(point[0], tz=ZoneInfo("US/Mountain"))
                    )
                    values.append(float(point[1]) / unit_divisor)
                else:
                    times.append("")
                    values.append("")
            graph_data[current_label] = {"times": times, "values": values}
    else:
        for metric in response:
            current_label = metric["metric"][group_label] if group_label else "other"
            times = []
            values = []
            for point in metric["values"]:
                times.append(
                    datetime.fromtimestamp(point[0], tz=ZoneInfo("US/Mountain"))
                )
                values.append(float(point[1]) / unit_divisor)

            graph_data[current_label] = {"times": times, "values": values}

    return graph_data


def add_graph_data_traces(
    fig: Figure,
    graph_data: dict,
    stackgroup=None,
    name_prefix="",
    name_postfix="",
    **kwargs,
):
    """
    Adds all the data in the graph data to the figure in the given stack group.
    The name of each line is the key for the graph data surrounded by the name_prefix and name_postfix

    Args:
    - fig - the plotly figure to add Scatter Trace
    - stackgroup - the stackgroup each line has its area stacked with (None if you want unstacked)
    - name_prefix and name_postfix - name for each line is name_prefix+label+name_postfix Ex: if you want each line to be named {unit}-limit the name_postfix would be "-limit"
    - kwargs - all additional kwargs are dumped into the Scatter trace construction so if you want a specific type of line you can pass in plotly options there
    """

    for label, data in graph_data.items():
        fig.add_trace(
            Scatter(
                name=f"{name_prefix}{label}{name_postfix}",
                x=data["times"],
                y=data["values"],
                mode="lines",
                stackgroup=stackgroup,
                **kwargs,
            )
        )


def plot_target_cpu_graph(
    unit_re: str,
    host_re: str,
    start_time: datetime,
    end_time: datetime,
    policy_threshold: float | None = None,
    penalized_time: datetime | None = None,
    step="10s",
) -> Figure:
    """
    Makes a stacked line chart of CPU-usage in cores split by processes. Shows the cgroup limit and will draw the policy threshold if provided
    """

    #TODO fixme
    host_re += ".*"
    
    fig = Figure()

    # we are only interested in 'these' targets, filter all following queries
    target_filters = f'{{ unit=~"{ unit_re }", instance=~"{ host_re }"}}'

    # sum the total cpu usage of the unit
    total_usage_metric = 'systemd_unit_cpu_usage_ns'
    total_usage_query = f'sum(increase({ total_usage_metric }{ target_filters }[{ step }]))'

    # sum the total cpu of the processes in the unit, and graph
    proc_usage_metric = 'systemd_unit_proc_cpu_seconds'
    proc_usage_query = f'rate({ proc_usage_metric }{ target_filters }[{ step }])'
    proc_usage = prom.custom_query_range(proc_usage_query, start_time=start_time, end_time=end_time, step=step)
    print("proc_usage", proc_usage, proc_usage_query)
    proc_data = response_to_graph_data(response=proc_usage, group_label="proc", unit_divisor=1, omit_negative=True)
    add_graph_data_traces(fig, proc_data, stackgroup="process")

    # calculate the delta between the two totals, graph this as "other usage"
    delta_usage_query = f'(({ total_usage_query }) - ({ proc_usage_query })) > 0'
    delta_usage = prom.custom_query_range(delta_usage_query, start_time=start_time, end_time=end_time, step=step)
    print("delta_usage", delta_usage, delta_usage_query)
    delta_data = response_to_graph_data(response=delta_usage, unit_divisor=1_000_000_000, omit_negative=True)
    add_graph_data_traces(fig, delta_data, connectgaps=False, stackgroup="process", line={"color": "gray"})

    # discover if there are any hard quotas on the unit, and graph
    quota_metric = 'systemd_unit_cpu_quota_us_per_s'
    quota_query = f'{ quota_metric }{ target_filters }'
    quota = prom.custom_query_range(quota_query, start_time=start_time, end_time=end_time, step=step)
    quota_data = response_to_graph_data(response=quota, group_label="unit", unit_divisor=1_000_000_000, omit_negative=True)
    print("quota", quota, quota_query)
    delta_data = response_to_graph_data(response=delta_usage, unit_divisor=1_000_000_000, omit_negative=True)
    add_graph_data_traces(fig, quota_data, name_postfix="-Limit", connectgaps=False, line={"dash": "dot", "color": "red"})   

    if policy_threshold:
        fig.add_hline(
            policy_threshold,
            annotation_text="Policy Threshold",
            annotation_position="top left",
            line={"dash": "dot", "color": "grey"},
        )

    if penalized_time:
        fig.add_vline(
            penalized_time.timestamp() * 1000,
            annotation_text="Penalized",
            annotation_position="top left",
            line={"dash": "dash", "color": "grey"},
        )

    fig.update_layout(
        title=f"CPU Usage Report For {unit_re} on {host_re}",
        xaxis_title="Time",
        yaxis_title="Usage in Cores",
    )

    return fig


def plot_target_memory_graph(
    unit_re: str,
    host: str,
    start_time: datetime,
    end_time: datetime,
    policy_threshold: float | None = None,
    penalized_time: datetime | None = None,
    step="10s",
) -> Figure:
    """
    Makes a stacked line chart of Memory-usage in GiB split by processes. Shows the cgroup limit and will draw the policy threshold if provided
    """

    response = prom.custom_query_range(
        f'sum by (proc) (avg_over_time(procfs_pid_pss_bytes{{unit=~"{unit_re}", instance=~"{host}"}}[{step}]))',
        start_time=start_time,
        end_time=end_time,
        step=step,
    )

    pid_memory_data = response_to_graph_data(response, "proc", unit_divisor=GIB)

    response = prom.custom_query_range(
        f'systemd_unit_memory_max_bytes{{unit=~"{unit_re}", instance=~"{host}"}}',
        start_time=start_time,
        end_time=end_time,
        step=step,
    )

    memory_limit_data = response_to_graph_data(
        response, "unit", unit_divisor=GIB, omit_negative=True
    )

    response = prom.custom_query_range(
        f'((sum (systemd_unit_memory_current_bytes{{unit=~"{unit_re}", instance=~"{host}"}})) - (sum (procfs_pid_pss_bytes{{unit=~"{unit_re}", instance=~"{host}"}}))) > 0',
        start_time=start_time,
        end_time=end_time,
        step=step,
    )

    other_proc_data = response_to_graph_data(
        response, unit_divisor=GIB, omit_negative=True
    )

    fig = Figure()

    add_graph_data_traces(
        fig,
        other_proc_data,
        connectgaps=False,
        stackgroup="process",
        line={"color": "gray"},
    )
    add_graph_data_traces(fig, pid_memory_data, stackgroup="process")
    add_graph_data_traces(
        fig,
        memory_limit_data,
        name_postfix="-Limit",
        connectgaps=False,
        line={"dash": "dot", "color": "red"},
    )

    if policy_threshold:
        fig.add_hline(
            policy_threshold,
            annotation_text="Policy Threshold",
            annotation_position="top left",
            line={"dash": "dot", "color": "grey"},
        )

    if penalized_time:
        fig.add_vline(
            penalized_time.timestamp() * 1000,
            annotation_text="Penalized",
            annotation_position="top left",
            line={"dash": "dash", "color": "grey"},
        )

    fig.update_layout(
        title=f"Memory Usage Report For {unit_re} on {host}",
        xaxis_title="Time",
        yaxis_title="Usage in GiB",
    )

    return fig


def instant_response_to_data(response: dict, group_label: str, unit_divisor=1) -> dict:
    pie_data = dict()

    for metric in response:
        current_label = metric["metric"][group_label]

        pie_data[current_label] = float(metric["value"][1]) / unit_divisor

    return pie_data


def plot_target_proc_cpu_usage_pie(
    unit_re: str, host: str, start_time: datetime, end_time: datetime
) -> Figure:
    total_seconds = int((end_time - start_time).total_seconds())
    response = prom.custom_query(
        f'rate(procfs_pid_cpu_usage_ns{{unit=~"{unit_re}", instance=~"^{host}"}}[{total_seconds}s])',
        params=dict(time=end_time.timestamp()),
    )

    cpu_pie_data: dict = instant_response_to_data(
        response, group_label="proc", unit_divisor=1_000_000_000
    )

    response = prom.custom_query(
        f'((sum (increase(systemd_unit_cpu_usage_ns{{unit=~"{unit_re}", instance=~"{host}"}}[{total_seconds}s]))) - (sum (increase(procfs_pid_cpu_usage_ns{{unit=~"{unit_re}", instance=~"{host}"}}[{total_seconds}s])))) > 0',
    )

    cpu_pie_data["other"] = sum(
        [float(metric["value"][1]) / GIB for metric in response]
    )

    fig = Figure(
        data=Pie(labels=list(cpu_pie_data.keys()), values=list(cpu_pie_data.values()))
    )

    fig.update_layout(
        title=f"Process % CPU Usage",
    )

    return fig


def plot_target_proc_memory_usage_pie(
    unit_re: str, host: str, start_time: datetime, end_time: datetime
) -> Figure:
    total_seconds = int((end_time - start_time).total_seconds())
    response = prom.custom_query(
        f'avg_over_time(procfs_pid_pss_bytes{{unit=~"{unit_re}", instance=~"{host}"}}[{total_seconds}s])',
        params=dict(time=end_time.timestamp()),
    )
    cpu_pie_data: dict = instant_response_to_data(
        response, group_label="proc", unit_divisor=GIB
    )

    response = prom.custom_query(
        f'((sum (avg_over_time(systemd_unit_memory_current_bytes{{unit=~"{unit_re}", instance=~"{host}"}}[{total_seconds}s]))) - (sum (avg_over_time(procfs_pid_pss_bytes{{unit=~"{unit_re}", instance=~"{host}"}}[{total_seconds}s])))) > 0',
    )

    cpu_pie_data["other"] = sum(
        [float(metric["value"][1]) / GIB for metric in response]
    )

    fig = Figure(
        data=Pie(labels=list(cpu_pie_data.keys()), values=list(cpu_pie_data.values()))
    )

    fig.update_layout(
        title=f"Process % Memory Usage",
    )

    return fig


def plot_violation_cpu_graph(violation: Violation, step="10s") -> Figure:
    start_time = violation.timestamp - violation.policy.timewindow
    end_time = violation.expiration
    step = align_with_prom_limit(start_time, end_time, step)

    return plot_target_cpu_graph(
        violation.target.unit,
        violation.target.host,
        start_time=start_time,
        end_time=end_time,
        policy_threshold=violation.policy.query_params.get("cpu_threshold", None),
        penalized_time=violation.timestamp,
        step=step,
    )


def plot_violation_memory_graph(violation: Violation, step="10s") -> Figure:
    start_time = violation.timestamp - violation.policy.timewindow
    end_time = violation.expiration
    step = align_with_prom_limit(start_time, end_time, step)

    return plot_target_memory_graph(
        violation.target.unit,
        violation.target.host,
        start_time=start_time,
        end_time=end_time,
        policy_threshold=violation.policy.query_params.get("memory_threshold", None),
        penalized_time=violation.timestamp,
        step=step,
    )


def plot_violation_proc_cpu_usage_pie(violation: Violation) -> Figure:
    start_time = violation.timestamp - violation.policy.timewindow
    end_time = violation.timestamp

    return plot_target_proc_cpu_usage_pie(
        violation.target.unit,
        violation.target.host,
        start_time=start_time,
        end_time=end_time,
    )


def plot_violation_proc_memory_usage_pie(violation: Violation) -> Figure:
    start_time = violation.timestamp - violation.policy.timewindow
    end_time = violation.timestamp

    return plot_target_proc_memory_usage_pie(
        violation.target.unit,
        violation.target.host,
        start_time=start_time,
        end_time=end_time,
    )
