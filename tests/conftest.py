import pytest
import os
from pathlib import Path

from marklogic import Client

from txnextgen_backend import SemanticGraph
from txnextgen_backend.config import get_settings
from txnextgen_backend.datastore import get_ml_client
from txnextgen_backend.ext_sources.ebay import EbayJsonParser

get_settings().datastore_backend_uri = "http://taxtime-2023.r4.v-lad.org:8030"


@pytest.fixture
def test_dir():
    return Path(__file__).parent


@pytest.fixture
def client():
    return get_ml_client()


@pytest.fixture()
def data_dir(test_dir):
    return Path(test_dir).parent / "sample_data"


@pytest.fixture
def sample_archive(data_dir):
    return data_dir / "documents-Tx2023-pmox-000.zip"


@pytest.fixture
def taxtime_test_graph():
    base_url = get_settings().datastore_backend_uri
    return SemanticGraph("taxtime-test", base_url=base_url)


@pytest.fixture()
def email_obj_uri():
    return "https://taxtime.r4.v-lad.org/v1/email/doc/email/2022/17e21613c0eef943.xml"


@pytest.fixture
def ebay_parser(data_dir):
    parser = EbayJsonParser()
    parser.parse_data_file(data_dir / "ebay_orders_sample.1.json")
    return parser


@pytest.fixture(autouse=True)
def prepare_test_database(client: Client):
    """
    Deletes any documents created by other tests to ensure a 'clean' database before a
    test runs. Does not delete documents in the 'test-data' collection which is intended
    to contain all the documents loaded by the test-app. A user with the 'admin' role
    is used so that temporal documents can be deleted.
    """
    query = "cts:uris((), (), cts:not-query(cts:collection-query('test-data'))) \
        ! xdmp:document-delete(.)"
    # response = admin_client.post(
    #     "v1/eval",
    #     headers={"Content-type": "application/x-www-form-urlencoded"},
    #     data={"xquery": query},
    # )
    # assert 200 == response.status_code
