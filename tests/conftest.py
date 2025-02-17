import pytest
from pathlib import Path

curdir = Path(__file__).parent


@pytest.fixture
def paper():
    """Returns a search query that mimics the one shown in the paper
    for electrically-insulating heat sinks.
    """
    from aflow import search, K

    result = (
        search(batch_size=20)
        .select(K.agl_thermal_conductivity_300K)
        .filter(K.Egap >= 6)
        .orderby(K.agl_thermal_conductivity_300K, True)
    )

    # Let's pre-fill the responses from the saved JSON files so that the tests
    # run faster *and* so that the results are predictable.
    import json

    result._N = 912

    n = -1
    with open(curdir / "data0.json") as f:
        response = json.loads(f.read())
        result.responses[n] = response
    n = -2
    with open(curdir / "data1.json") as f:
        response = json.loads(f.read())
        result.responses[n] = response

    return result[0:40]
