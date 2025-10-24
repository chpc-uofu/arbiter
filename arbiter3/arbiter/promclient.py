import requests
from urllib.parse import urljoin
from collections import defaultdict
from typing import NamedTuple

class Series(NamedTuple):
    timestamp: int
    value: str


class Vector(NamedTuple):
    metric: dict[str, str]
    value: Series


class Matrix(NamedTuple):
    metric: dict[str, str]
    values: list[Series]

def parse_vector_result(result: dict[str, str]) -> list[Vector]:
    vectors = []
    for r in result:
        metric = r['metric']
        value = Series(*r['value'])
        vector = Vector(metric, value)
        vectors.append(vector)
    return vectors


def parse_matrix_result(result: dict[str, str]) -> list[Matrix]:
    matrices = []
    for r in result:
        labels = r["metric"]
        series = []
        for stamp, value in r["values"]:
            series.append(Series(stamp, value))
        matrices.append(Matrix(labels, series))
    return matrices


class PrometheusSession(requests.Session):
    def __init__(self, base_url, username=None, password=None, verify=True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_url = base_url if base_url.endswith("/") else base_url + "/"
        self.headers.update({"Content-Type": "application/json"})
        if username and password:
            self.auth = requests.auth.HTTPBasicAuth(username, password)
        self.verify = verify


    def get(self, path, *args, **kwargs):
        return super().get(urljoin(self.base_url, path), *args, **kwargs)


    def validate_response(self, response: requests.Response):
        response.raise_for_status()
        return response.json()


    def query(self, query, time=None, timeout=None) -> list[Vector] | list[Matrix]:
        """
        https://prometheus.io/docs/prometheus/latest/querying/api/#instant-queries
        """
        
        params = {"query": query}

        if time:
            params["time"] = time

        if timeout:
            params["timeout"] = timeout

        response = self.get("api/v1/query", params=params, timeout=timeout)
        data = self.validate_response(response)['data']
        match data['resultType']:
            case 'matrix':
                return parse_matrix_result(data['result'])
            case 'vector':
                return parse_vector_result(data['result'])
            case _:
                raise NotImplementedError


    def query_range(self, query, start, end, step, timeout=None) -> list[Matrix]:
        """
        https://prometheus.io/docs/prometheus/latest/querying/api/#range-queries
        """

        params = {
            "query": query,
            "start": start,
            "end": end,
            "step": step,
        }

        if timeout:
            params['timeout'] = timeout

        response = self.get("api/v1/query_range", params=params, timeout=timeout)
        data = self.validate_response(response)['data']
        match data['resultType']:
            case 'matrix':
                return parse_matrix_result(data['result'])
            case _:
                raise NotImplementedError 
            

def sort_matrices_by_avg(matrices: list[Matrix]) -> list[Matrix]:
    averages = []
    for m in matrices:
        total = sum([float(s.value) for s in m.values])
        count = len(m.values)
        if count == 0:
            continue
        average = total / count
        averages.append( (average, m) )
    averages = sorted(averages, key=lambda a: a[0], reverse=True)
    return [r[1] for r in averages]


def combine_last_matrices(matrices: list[Matrix], n: int) -> list[Matrix]:
    if len(matrices) < n:
        return matrices
    keep = matrices[:n]
    combine = matrices[n:]
    other_sums = defaultdict(int)
    for m in combine:
        for ts, v in m.values:
            other_sums[ts] += float(v)
    
    if sum(other_sums.values()) == 0:
        return keep
    other_values = [Series(ts, v) for ts, v in other_sums.items()]
    other_matrix = Matrix(metric=dict(proc='other**'), values=other_values)

    keep.append(other_matrix)
    return keep