# *******************************************************
# Copyright (c) Broadcom, Inc. 2020-2024. All Rights Reserved. Carbon Black.
# SPDX-License-Identifier: MIT
# *******************************************************
# *
# * DISCLAIMER. THIS PROGRAM IS PROVIDED TO YOU "AS IS" WITHOUT
# * WARRANTIES OR CONDITIONS OF ANY KIND, WHETHER ORAL OR WRITTEN,
# * EXPRESS OR IMPLIED. THE AUTHOR SPECIFICALLY DISCLAIMS ANY IMPLIED
# * WARRANTIES OR CONDITIONS OF MERCHANTABILITY, SATISFACTORY QUALITY,
# * NON-INFRINGEMENT AND FITNESS FOR A PARTICULAR PURPOSE.

"""Testing functions which generate a v6 compatible out from using v7 APIs."""
import pytest

# Import Base Alert since we're testing backwards compatibility
from cbc_sdk.platform import BaseAlert
from cbc_sdk.rest_api import CBCloudAPI
from tests.unit.fixtures.platform.mock_alert_v6_v7_compatibility import (
    ALERT_V6_INFO_CB_ANALYTICS_SDK_1_4_3,
    ALERT_V6_INFO_WATCHLIST_SDK_1_4_3,
    ALERT_V6_INFO_DEVICE_CONTROL_SDK_1_4_3,
    ALERT_V6_INFO_HBFW_SDK_1_4_3,
    ALERT_V6_INFO_CONTAINER_RUNTIME_SDK_1_4_3,
    GET_ALERT_v7_CB_ANALYTICS_RESPONSE,
    GET_ALERT_v7_WATCHLIST_RESPONSE,
    GET_ALERT_v7_DEVICE_CONTROL_RESPONSE,
    GET_ALERT_v7_HBFW_RESPONSE,
    GET_ALERT_v7_CONTAINER_RUNTIME_RESPONSE
)

from tests.unit.fixtures.CBCSDKMock import CBCSDKMock


@pytest.fixture(scope="function")
def cb():
    """Create CBCloudAPI singleton"""
    return CBCloudAPI(url="https://example.com", org_key="test", token="abcd/1234", ssl_verify=False)


@pytest.fixture(scope="function")
def cbcsdk_mock(monkeypatch, cb):
    """Mocks CBC SDK for unit tests"""
    return CBCSDKMock(monkeypatch, cb)


# ==================================== UNIT TESTS BELOW ====================================
# Fields that are special - consider extending tests later
# remediation can be empty string in v6, has "NO_REASON" in v7
COMPLEX_MAPPING_V6 = {
    "threat_cause_actor_name",  # on CB Analytics, the record is truncated on v6 so will not match
    "process_name"  # just the file name on v6, full path on v7
}

# Fields on the v6 base or common alert object that do not have an equivalent in v7
BASE_FIELDS_V6 = {
    "alert_classification",
    "category",
    "comment",
    "group_details",
    "threat_activity_c2",
    "threat_cause_threat_category",
    "threat_cause_actor_process_pid"
}

# Fields on the v6 CB Analytics alert object that do not have an equivalent in v7
CB_ANALYTICS_FIELDS_V6 = {
    "blocked_threat_category",
    "kill_chain_status",
    "not_blocked_threat_category",
    "threat_activity_c2",
    "threat_activity_dlp",
    "threat_activity_phish",
    "threat_cause_vector"
}

# Fields on the v6 Device Control alert object that do not have an equivalent in v7
DEVICE_CONTROL_FIELDS_V6 = {
    "threat_cause_vector"
}

# Fields on the v6 Container Runtime alert object that do not have an equivalent in v7
CONTAINER_RUNTIME_FIELDS_V6 = {
    "workload_id",
    "target_value"
}

# Fields on the v6 Watchlist alert object that do not have an equivalent in v7
WATCHLIST_FIELDS_V6 = {
    "count",
    "document_guid",
    "threat_cause_vector",
    "threat_indicators"
}

# Aggregate all the alert type fields
ALL_FIELDS_V6 = (CB_ANALYTICS_FIELDS_V6 | BASE_FIELDS_V6 | DEVICE_CONTROL_FIELDS_V6 | WATCHLIST_FIELDS_V6
                 | CONTAINER_RUNTIME_FIELDS_V6)


@pytest.mark.parametrize("url, v7_api_response, v6_sdk_response", [
    ("/api/alerts/v7/orgs/test/alerts/6f1173f5-f921-8e11-2160-edf42b799333", GET_ALERT_v7_CB_ANALYTICS_RESPONSE,
     ALERT_V6_INFO_CB_ANALYTICS_SDK_1_4_3),
    ("/api/alerts/v7/orgs/test/alerts/f6af290d-6a7f-461c-a8af-cf0d24311105", GET_ALERT_v7_WATCHLIST_RESPONSE,
     ALERT_V6_INFO_WATCHLIST_SDK_1_4_3),
    ("/api/alerts/v7/orgs/test/alerts/46b419c8-3d67-ead8-dbf1-9d8417610fac", GET_ALERT_v7_CONTAINER_RUNTIME_RESPONSE,
     ALERT_V6_INFO_CONTAINER_RUNTIME_SDK_1_4_3),
    ("/api/alerts/v7/orgs/test/alerts/2be0652f-20bc-3311-9ded-8b873e28d830", GET_ALERT_v7_HBFW_RESPONSE,
     ALERT_V6_INFO_HBFW_SDK_1_4_3),
    ("/api/alerts/v7/orgs/test/alerts/b6a7e48b-1d14-11ee-a9e0-888888888788", GET_ALERT_v7_DEVICE_CONTROL_RESPONSE,
     ALERT_V6_INFO_DEVICE_CONTROL_SDK_1_4_3)
])
def test_v7_generate_v6_json(cbcsdk_mock, url, v7_api_response, v6_sdk_response):
    """
    Test the generation of a v6 to_json output

    Compare what is generated by the current SDK with expected from SDK 1.4.3
    Parameterization above is used to call this test multiple times to test different alert types
    """
    # set up the mock request and execute the mock v7 API call
    cbcsdk_mock.mock_request("GET", url, v7_api_response)
    api = cbcsdk_mock.api
    alert = api.select(BaseAlert, v6_sdk_response.get("id"))
    # generate the json output from the v7 API response in the v6 format
    alert_v6_from_v7 = alert.to_json("v6")

    # Recursively compare each field in the fixture v6 with that produced using the to_json method in the current SDK.
    # The v6 fixture were generated with an earlier version of the SDK (1.4.3)
    # The v7 fixtures were generated with v7 API calls
    # That the output of the current to_json("v6") method equals the v6 fixture is what is being tested
    for key in v6_sdk_response:
        """Check inner dictionaries"""
        if isinstance(v6_sdk_response.get(key), dict):
            check_dict(v6_sdk_response.get(key), alert_v6_from_v7.get(key), key, v6_sdk_response.get("type"))
        else:
            # send the dict containing the field as the field will not always exist in alert_v6_from_v7
            check_field(v6_sdk_response, alert_v6_from_v7, key, v6_sdk_response.get("type"))


def check_dict(alert_v6, alert_v6_from_v7, key, alert_type):
    """
    Make some generic checks for fields

    Key should be the label, and each of alert_v6 and alert_v6_from_v7 should be dicts
    """
    # This method is expecting a dict input parameter. Verify.
    assert (isinstance(alert_v6, dict)), "Function check_dict called with incorrect argument types"

    if key in COMPLEX_MAPPING_V6:
        return
    # Fields that are deprecated will be in v6 and should not be in v7
    assert not (
        key in BASE_FIELDS_V6 and alert_v6_from_v7 is not None and key in alert_v6_from_v7
    ), ("ERROR: Field is deprecated and does not exist in v7. Expected: Not in to_json(v6). Actual: was incorrectly "
        "included. Source: BASE_FIELDS_V6. Key: {}").format(key)

    # fields from cb analytics that are not in v7. No mapping available
    assert not (
        alert_type == "CB_ANALYTICS" and key in CB_ANALYTICS_FIELDS_V6 and alert_v6_from_v7 is not None
        and key in alert_v6_from_v7
    ), ("ERROR: Field is deprecated and does not exist in v7. Expected: Not in to_json(v6). Actual: was incorrectly "
        "included. Source: CB_ANALYTICS_FIELDS_V6. Key: {}").format(key)

    # fields from container runtime that are not in v7. No mapping available
    assert not (alert_type == "CONTAINER_RUNTIME" and key in CONTAINER_RUNTIME_FIELDS_V6
                and alert_v6_from_v7 is not None and key in alert_v6_from_v7), (
        ("ERROR: Field is deprecated and does not exist in v7. Expected: Not in to_json(v6). Actual: was incorrectly "
         "included. Source: CONTAINER_RUNTIME_FIELDS_V6. Key: {}").format(key))

    # no fields removed in v7 for host based firewall alerts
    # fields from device control that are not in v7. No mapping available
    assert not (
        alert_type == "DEVICE_CONTROL" and key in DEVICE_CONTROL_FIELDS_V6 and alert_v6_from_v7 is not None
        and key in alert_v6_from_v7
    ), ("ERROR: Field is deprecated and does not exist in v7. Expected: Not in to_json(v6). Actual: was incorrectly "
        "included. Source: DEVICE_CONTROL_FIELDS_V6. Key: {}").format(
        key)

    # fields from watchlist alert that are not in v7. No mapping available
    assert not (
        alert_type == "WATCHLIST" and key in WATCHLIST_FIELDS_V6 and alert_v6_from_v7 is not None
        and key in alert_v6_from_v7
    ), ("ERROR: Field is deprecated and does not exist in v7. Expected: Not in to_json(v6). Actual: was incorrectly "
        "included. Source: WATCHLIST_FIELDS_V6. Key: {}").format(key)

    # If the key is in v6 and correctly not in v7 the earlier asserts will have passed
    # Do not inspect the inner dict
    if key not in ALL_FIELDS_V6:
        for inner_key in alert_v6:
            if isinstance(alert_v6.get(inner_key), dict):
                check_dict(alert_v6.get(inner_key), alert_v6_from_v7.get(inner_key), inner_key, alert_type)
            else:
                check_field(alert_v6, alert_v6_from_v7, inner_key, alert_type)


def check_field(alert_v6, alert_v6_from_v7, key, alert_type):
    """
    Check rules about when fields should and should not be mapped

    Orgs are dictionaries, key is the field being evaluated.
    End with a value comparison
    """
    if key in COMPLEX_MAPPING_V6:
        return
    # Fields that are deprecated will be in v6 and should not be in v7
    assert not (
        key in BASE_FIELDS_V6 and key in alert_v6_from_v7
    ), ("ERROR: Field is deprecated and does not exist in v7. Expected: Not in to_json(v6). Actual: was incorrectly "
        "included. Source: BASE_FIELDS_V6. Key: {}").format(key)

    # fields from cb analytics that are not in v7. No mapping available
    assert not (
        alert_type == "CB_ANALYTICS" and key in CB_ANALYTICS_FIELDS_V6 and key in alert_v6_from_v7
    ), ("ERROR: Field is deprecated and does not exist in v7. Expected: Not in to_json(v6). Actual: was incorrectly "
        "included. Source: CB_ANALYTICS_FIELDS_V6. Key: {}").format(key)

    # container runtime alerts
    # fields from watchlist alert that are not in v7. No mapping available
    assert not (alert_type == "CONTAINER_RUNTIME" and key in CONTAINER_RUNTIME_FIELDS_V6 and key in alert_v6_from_v7), (
        ("ERROR: Field is deprecated and does not exist in v7. Expected: Not in to_json(v6). Actual: was incorrectly "
         "included. Source: CONTAINER_RUNTIME_FIELDS_V6. Key: {}").format(key))

    # no fields removed in v7 for host based firewall alerts
    # fields from device control that are not in v7. No mapping available
    assert not (
        alert_type == "DEVICE_CONTROL" and key in DEVICE_CONTROL_FIELDS_V6 and key in alert_v6_from_v7
    ), ("ERROR: Field is deprecated and does not exist in v7. Expected: Not in to_json(v6). Actual: was incorrectly "
        "included. Source: DEVICE_CONTROL_FIELDS_V6. Key: {}").format(
        key)

    # fields from watchlist alert that are not in v7. No mapping available
    assert not (
        alert_type == "WATCHLIST" and key in WATCHLIST_FIELDS_V6 and key in alert_v6_from_v7
    ), ("ERROR: Field is deprecated and does not exist in v7. Expected: Not in to_json(v6). Actual: was incorrectly "
        "included. Source: WATCHLIST_FIELDS_V6. Key: {}").format(key)

    if key not in ALL_FIELDS_V6:
        assert (alert_v6.get(key) == alert_v6_from_v7.get(key)
                or (alert_v6.get(key) == "" and alert_v6_from_v7.get(key) is None)
                or (alert_v6.get(key) == 0 and alert_v6_from_v7.get(key) is None)  # device info on CONTAINER_RUNTIME
                ), "ERROR: Values do not match {} - v6: {} v7: {}".format(key, alert_v6.get(key),
                                                                          alert_v6_from_v7.get(key))


def test_set_alert_ids(cbcsdk_mock):
    """Test legacy set_alert_ids method"""
    def on_post(url, body, **kwargs):
        assert body == {
            "criteria": {
                "id": [
                    "123"
                ]
            },
            "rows": 1
        }
        return {"results": [{"id": "S0L0", "org_key": "test", "threat_id": "B0RG",
                             "workflow": {"status": "OPEN"}}], "num_found": 1}
    cbcsdk_mock.mock_request('POST', "/api/alerts/v7/orgs/test/alerts/_search", on_post)
    api = cbcsdk_mock.api
    # no assertions, the check is that the post request is formed correctly.
    query = api.select(BaseAlert).set_alert_ids(["123"]).set_rows(1)
    len(query)


def test_set_create_time(cbcsdk_mock):
    """Test legacy set_create_time method"""
    def on_post(url, body, **kwargs):
        assert body == {
            "time_range": {
                "end": "2023-09-20T01:00:00.000000Z",
                "start": "2023-09-19T21:00:00.000000Z"
            },
            "rows": 1
        }
        return {"results": [{"id": "S0L0", "org_key": "test", "threat_id": "B0RG",
                             "workflow": {"status": "OPEN"}}], "num_found": 1}
    cbcsdk_mock.mock_request('POST', "/api/alerts/v7/orgs/test/alerts/_search", on_post)
    api = cbcsdk_mock.api
    # no assertions, the check is that the post request is formed correctly.
    query = api.select(BaseAlert).set_create_time(start="2023-09-19T21:00:00", end="2023-09-20T01:00:00").\
        set_rows(1)
    len(query)


def test_set_device_ids(cbcsdk_mock):
    """Test legacy set_device_ids method"""
    def on_post(url, body, **kwargs):
        assert body == {
            "criteria": {
                "device_id": [
                    123
                ]
            },
            "rows": 1
        }
        return {"results": [{"id": "S0L0", "org_key": "test", "threat_id": "B0RG",
                             "workflow": {"status": "OPEN"}}], "num_found": 1}
    cbcsdk_mock.mock_request('POST', "/api/alerts/v7/orgs/test/alerts/_search", on_post)
    api = cbcsdk_mock.api
    # no assertions, the check is that the post request is formed correctly.
    query = api.select(BaseAlert).set_device_ids([123]).set_rows(1)
    len(query)


def test_set_device_names(cbcsdk_mock):
    """Test legacy template method"""
    def on_post(url, body, **kwargs):
        assert body == {
            "criteria": {
                "device_name": [
                    "123"
                ]
            },
            "rows": 1
        }
        return {"results": [{"id": "S0L0", "org_key": "test", "threat_id": "B0RG",
                             "workflow": {"status": "OPEN"}}], "num_found": 1}

    cbcsdk_mock.mock_request('POST', "/api/alerts/v7/orgs/test/alerts/_search", on_post)
    api = cbcsdk_mock.api
    # no assertions, the check is that the post request is formed correctly.
    query = api.select(BaseAlert).set_device_names(["123"]).set_rows(1)
    len(query)


def test_set_device_os(cbcsdk_mock):
    """Test legacy set_device_os method"""
    def on_post(url, body, **kwargs):
        assert body == {
            "criteria": {
                "device_os": [
                    "LINUX"
                ]
            },
            "rows": 1
        }
        return {"results": [{"id": "S0L0", "org_key": "test", "threat_id": "B0RG",
                             "workflow": {"status": "OPEN"}}], "num_found": 1}

    cbcsdk_mock.mock_request('POST', "/api/alerts/v7/orgs/test/alerts/_search", on_post)
    api = cbcsdk_mock.api
    # no assertions, the check is that the post request is formed correctly.
    query = api.select(BaseAlert).set_device_os(["LINUX"]).set_rows(1)
    len(query)


def test_set_device_os_versions(cbcsdk_mock):
    """Test legacy set_device_os_versions method"""
    def on_post(url, body, **kwargs):
        assert body == {
            "criteria": {
                "device_os_version": [
                    "123"
                ]
            },
            "rows": 1
        }
        return {"results": [{"id": "S0L0", "org_key": "test", "threat_id": "B0RG",
                             "workflow": {"status": "OPEN"}}], "num_found": 1}

    cbcsdk_mock.mock_request('POST', "/api/alerts/v7/orgs/test/alerts/_search", on_post)
    api = cbcsdk_mock.api
    # no assertions, the check is that the post request is formed correctly.
    query = api.select(BaseAlert).set_device_os_versions(["123"]).set_rows(1)
    len(query)


def test_set_device_username(cbcsdk_mock):
    """Test legacy set_device_username method"""
    def on_post(url, body, **kwargs):
        assert body == {
            "criteria": {
                "device_username": [
                    "123"
                ]
            },
            "rows": 1
        }
        return {"results": [{"id": "S0L0", "org_key": "test", "threat_id": "B0RG",
                             "workflow": {"status": "OPEN"}}], "num_found": 1}

    cbcsdk_mock.mock_request('POST', "/api/alerts/v7/orgs/test/alerts/_search", on_post)
    api = cbcsdk_mock.api
    # no assertions, the check is that the post request is formed correctly.
    query = api.select(BaseAlert).set_device_username(["123"]).set_rows(1)
    len(query)


def test_set_legacy_alert_ids(cbcsdk_mock):
    """Test legacy set_legacy_alert_ids method"""
    def on_post(url, body, **kwargs):
        assert body == {
            "criteria": {
                "id": [
                    "123"
                ]
            },
            "rows": 1
        }
        return {"results": [{"id": "S0L0", "org_key": "test", "threat_id": "B0RG",
                             "workflow": {"status": "OPEN"}}], "num_found": 1}

    cbcsdk_mock.mock_request('POST', "/api/alerts/v7/orgs/test/alerts/_search", on_post)
    api = cbcsdk_mock.api
    # no assertions, the check is that the post request is formed correctly.
    query = api.select(BaseAlert).set_legacy_alert_ids(["123"]).set_rows(1)
    len(query)


def test_set_policy_ids(cbcsdk_mock):
    """Test legacy set_policy_ids method"""
    def on_post(url, body, **kwargs):
        assert body == {
            "criteria": {
                "device_policy_id": [
                    123
                ]
            },
            "rows": 1
        }
        return {"results": [{"id": "S0L0", "org_key": "test", "threat_id": "B0RG",
                             "workflow": {"status": "OPEN"}}], "num_found": 1}

    cbcsdk_mock.mock_request('POST', "/api/alerts/v7/orgs/test/alerts/_search", on_post)
    api = cbcsdk_mock.api
    # no assertions, the check is that the post request is formed correctly.
    query = api.select(BaseAlert).set_policy_ids([123]).set_rows(1)
    len(query)


def test_set_policy_names(cbcsdk_mock):
    """Test legacy policy_names method"""
    def on_post(url, body, **kwargs):
        assert body == {
            "criteria": {
                "device_policy": [
                    "policy name"
                ]
            },
            "rows": 1
        }
        return {"results": [{"id": "S0L0", "org_key": "test", "threat_id": "B0RG",
                             "workflow": {"status": "OPEN"}}], "num_found": 1}

    cbcsdk_mock.mock_request('POST', "/api/alerts/v7/orgs/test/alerts/_search", on_post)
    api = cbcsdk_mock.api
    # no assertions, the check is that the post request is formed correctly.
    query = api.select(BaseAlert).set_policy_names(["policy name"]).set_rows(1)
    len(query)


def test_set_process_names(cbcsdk_mock):
    """Test legacy set_process_names method"""
    def on_post(url, body, **kwargs):
        assert body == {
            "criteria": {
                "process_name": [
                    "123"
                ]
            },
            "rows": 1
        }
        return {"results": [{"id": "S0L0", "org_key": "test", "threat_id": "B0RG",
                             "workflow": {"status": "OPEN"}}], "num_found": 1}

    cbcsdk_mock.mock_request('POST', "/api/alerts/v7/orgs/test/alerts/_search", on_post)
    api = cbcsdk_mock.api
    # no assertions, the check is that the post request is formed correctly.
    query = api.select(BaseAlert).set_process_names(["123"]).set_rows(1)
    len(query)


def test_set_process_sha256(cbcsdk_mock):
    """Test legacy set_process_sha256 method"""
    def on_post(url, body, **kwargs):
        assert body == {
            "criteria": {
                "process_sha256": [
                    "123"
                ]
            },
            "rows": 1
        }
        return {"results": [{"id": "S0L0", "org_key": "test", "threat_id": "B0RG",
                             "workflow": {"status": "OPEN"}}], "num_found": 1}

    cbcsdk_mock.mock_request('POST', "/api/alerts/v7/orgs/test/alerts/_search", on_post)
    api = cbcsdk_mock.api
    # no assertions, the check is that the post request is formed correctly.
    query = api.select(BaseAlert).set_process_sha256(["123"]).set_rows(1)
    len(query)


def test_set_reputations(cbcsdk_mock):
    """Test legacy set_reputations method"""
    def on_post(url, body, **kwargs):
        assert body == {
            "criteria": {
                "process_reputation": [
                    "PUP"
                ]
            },
            "rows": 1
        }
        return {"results": [{"id": "S0L0", "org_key": "test", "threat_id": "B0RG",
                             "workflow": {"status": "OPEN"}}], "num_found": 1}

    cbcsdk_mock.mock_request('POST', "/api/alerts/v7/orgs/test/alerts/_search", on_post)
    api = cbcsdk_mock.api
    # no assertions, the check is that the post request is formed correctly.
    query = api.select(BaseAlert).set_reputations(["PUP"]).set_rows(1)
    len(query)


def test_set_tags(cbcsdk_mock):
    """Test legacy set_tags method"""
    def on_post(url, body, **kwargs):
        assert body == {
            "criteria": {
                "tags": [
                    "123"
                ]
            },
            "rows": 1
        }
        return {"results": [{"id": "S0L0", "org_key": "test", "threat_id": "B0RG",
                             "workflow": {"status": "OPEN"}}], "num_found": 1}

    cbcsdk_mock.mock_request('POST', "/api/alerts/v7/orgs/test/alerts/_search", on_post)
    api = cbcsdk_mock.api
    # no assertions, the check is that the post request is formed correctly.
    query = api.select(BaseAlert).set_tags(["123"]).set_rows(1)
    len(query)


def test_set_target_priorities(cbcsdk_mock):
    """Test legacy set_target_priorities method"""
    def on_post(url, body, **kwargs):
        assert body == {
            "criteria": {
                "device_target_value": [
                    "LOW"
                ]
            },
            "rows": 1
        }
        return {"results": [{"id": "S0L0", "org_key": "test", "threat_id": "B0RG",
                             "workflow": {"status": "OPEN"}}], "num_found": 1}

    cbcsdk_mock.mock_request('POST', "/api/alerts/v7/orgs/test/alerts/_search", on_post)
    api = cbcsdk_mock.api
    # no assertions, the check is that the post request is formed correctly.
    query = api.select(BaseAlert).set_target_priorities(["LOW"]).set_rows(1)
    len(query)


def test_set_external_device_ids(cbcsdk_mock):
    """Test legacy set_external_device_ids method"""
    def on_post(url, body, **kwargs):
        assert body == {
            "criteria": {
                "device_id": [
                    "123"
                ]
            },
            "rows": 1
        }
        return {"results": [{"id": "S0L0", "org_key": "test", "threat_id": "B0RG",
                             "workflow": {"status": "OPEN"}}], "num_found": 1}

    cbcsdk_mock.mock_request('POST', "/api/alerts/v7/orgs/test/alerts/_search", on_post)
    api = cbcsdk_mock.api
    # no assertions, the check is that the post request is formed correctly.
    query = api.select(BaseAlert).set_external_device_ids(["123"]).set_rows(1)
    len(query)


def test_set_workload_names(cbcsdk_mock):
    """Test legacy set_workload_names method"""
    def on_post(url, body, **kwargs):
        assert body == {
            "criteria": {
                "k8s_workload_name": [
                    "123"
                ]
            },
            "rows": 1
        }
        return {"results": [{"id": "S0L0", "org_key": "test", "threat_id": "B0RG",
                             "workflow": {"status": "OPEN"}}], "num_found": 1}

    cbcsdk_mock.mock_request('POST', "/api/alerts/v7/orgs/test/alerts/_search", on_post)
    api = cbcsdk_mock.api
    # no assertions, the check is that the post request is formed correctly.
    query = api.select(BaseAlert).set_workload_names(["123"]).set_rows(1)
    len(query)


def test_set_cluster_names(cbcsdk_mock):
    """Test legacy set_cluster_names method"""
    def on_post(url, body, **kwargs):
        assert body == {
            "criteria": {
                "k8s_cluster": [
                    "123"
                ]
            },
            "rows": 1
        }
        return {"results": [{"id": "S0L0", "org_key": "test", "threat_id": "B0RG",
                             "workflow": {"status": "OPEN"}}], "num_found": 1}

    cbcsdk_mock.mock_request('POST', "/api/alerts/v7/orgs/test/alerts/_search", on_post)
    api = cbcsdk_mock.api
    # no assertions, the check is that the post request is formed correctly.
    query = api.select(BaseAlert).set_cluster_names(["123"]).set_rows(1)
    len(query)


def test_set_namespaces(cbcsdk_mock):
    """Test legacy set_namespaces method"""
    def on_post(url, body, **kwargs):
        assert body == {
            "criteria": {
                "k8s_namespace": [
                    "123"
                ]
            },
            "rows": 1
        }
        return {"results": [{"id": "S0L0", "org_key": "test", "threat_id": "B0RG",
                             "workflow": {"status": "OPEN"}}], "num_found": 1}

    cbcsdk_mock.mock_request('POST', "/api/alerts/v7/orgs/test/alerts/_search", on_post)
    api = cbcsdk_mock.api
    # no assertions, the check is that the post request is formed correctly.
    query = api.select(BaseAlert).set_namespaces(["123"]).set_rows(1)
    len(query)


def test_set_ports(cbcsdk_mock):
    """Test legacy set_ports method"""
    def on_post(url, body, **kwargs):
        assert body == {
            "criteria": {
                "netconn_local_port": [
                    123
                ]
            },
            "rows": 1
        }
        return {"results": [{"id": "S0L0", "org_key": "test", "threat_id": "B0RG",
                             "workflow": {"status": "OPEN"}}], "num_found": 1}

    cbcsdk_mock.mock_request('POST', "/api/alerts/v7/orgs/test/alerts/_search", on_post)
    api = cbcsdk_mock.api
    # no assertions, the check is that the post request is formed correctly.
    query = api.select(BaseAlert).set_ports([123]).set_rows(1)
    len(query)


def test_set_protocols(cbcsdk_mock):
    """Test legacy set_protocols method"""
    def on_post(url, body, **kwargs):
        assert body == {
            "criteria": {
                "netconn_protocol": [
                    "PROTOCOL"
                ]
            },
            "rows": 1
        }
        return {"results": [{"id": "S0L0", "org_key": "test", "threat_id": "B0RG",
                             "workflow": {"status": "OPEN"}}], "num_found": 1}

    cbcsdk_mock.mock_request('POST', "/api/alerts/v7/orgs/test/alerts/_search", on_post)
    api = cbcsdk_mock.api
    # no assertions, the check is that the post request is formed correctly.
    query = api.select(BaseAlert).set_protocols(["PROTOCOL"]).set_rows(1)
    len(query)


def test_set_remote_domains(cbcsdk_mock):
    """Test legacy set_remote_domains method"""
    def on_post(url, body, **kwargs):
        assert body == {
            "criteria": {
                "netconn_remote_domain": [
                    "123"
                ]
            },
            "rows": 1
        }
        return {"results": [{"id": "S0L0", "org_key": "test", "threat_id": "B0RG",
                             "workflow": {"status": "OPEN"}}], "num_found": 1}

    cbcsdk_mock.mock_request('POST', "/api/alerts/v7/orgs/test/alerts/_search", on_post)
    api = cbcsdk_mock.api
    # no assertions, the check is that the post request is formed correctly.
    query = api.select(BaseAlert).set_remote_domains(["123"]).set_rows(1)
    len(query)


def test_set_remote_ips(cbcsdk_mock):
    """Test legacy set_remote_ips method"""
    def on_post(url, body, **kwargs):
        assert body == {
            "criteria": {
                "netconn_remote_ip": [
                    "1.2.3.4"
                ]
            },
            "rows": 1
        }
        return {"results": [{"id": "S0L0", "org_key": "test", "threat_id": "B0RG",
                             "workflow": {"status": "OPEN"}}], "num_found": 1}

    cbcsdk_mock.mock_request('POST', "/api/alerts/v7/orgs/test/alerts/_search", on_post)
    api = cbcsdk_mock.api
    # no assertions, the check is that the post request is formed correctly.
    query = api.select(BaseAlert).set_remote_ips(["1.2.3.4"]).set_rows(1)
    len(query)


def test_set_replica_ids(cbcsdk_mock):
    """Test legacy set_replica_ids method"""
    def on_post(url, body, **kwargs):
        assert body == {
            "criteria": {
                "k8s_pod_name": [
                    "123"
                ]
            },
            "rows": 1
        }
        return {"results": [{"id": "S0L0", "org_key": "test", "threat_id": "B0RG",
                             "workflow": {"status": "OPEN"}}], "num_found": 1}

    cbcsdk_mock.mock_request('POST', "/api/alerts/v7/orgs/test/alerts/_search", on_post)
    api = cbcsdk_mock.api
    # no assertions, the check is that the post request is formed correctly.
    query = api.select(BaseAlert).set_replica_ids(["123"]).set_rows(1)
    len(query)


def test_set_rule_ids(cbcsdk_mock):
    """Test legacy set_rule_ids method

    In SDK prior to 1.5.0 this was only supported for Container Runtime Alerts so will
    convert to k8s_rule_id.  For the post SDK 1.5.0 / Alert v7 API version, add_criteria()
    should be used for both k8s_rule_id and for other alert types, rule_id.
    """
    def on_post(url, body, **kwargs):
        assert body == {
            "criteria": {
                "k8s_rule_id": [
                    "123"
                ]
            },
            "rows": 1
        }
        return {"results": [{"id": "S0L0", "org_key": "test", "threat_id": "B0RG",
                             "workflow": {"status": "OPEN"}}], "num_found": 1}

    cbcsdk_mock.mock_request('POST', "/api/alerts/v7/orgs/test/alerts/_search", on_post)
    api = cbcsdk_mock.api
    # no assertions, the check is that the post request is formed correctly.
    query = api.select(BaseAlert).set_rule_ids(["123"]).set_rows(1)
    len(query)


def test_set_rule_names(cbcsdk_mock):
    """Test legacy set_rule_names method"""
    def on_post(url, body, **kwargs):
        assert body == {
            "criteria": {
                "k8s_rule": [
                    "123"
                ]
            },
            "rows": 1
        }
        return {"results": [{"id": "S0L0", "org_key": "test", "threat_id": "B0RG",
                             "workflow": {"status": "OPEN"}}], "num_found": 1}

    cbcsdk_mock.mock_request('POST', "/api/alerts/v7/orgs/test/alerts/_search", on_post)
    api = cbcsdk_mock.api
    # no assertions, the check is that the post request is formed correctly.
    query = api.select(BaseAlert).set_rule_names(["123"]).set_rows(1)
    len(query)


def test_set_workload_kinds(cbcsdk_mock):
    """Test legacy set_workload_kinds method"""
    def on_post(url, body, **kwargs):
        assert body == {
            "criteria": {
                "k8s_kind": [
                    "123"
                ]
            },
            "rows": 1
        }
        return {"results": [{"id": "S0L0", "org_key": "test", "threat_id": "B0RG",
                             "workflow": {"status": "OPEN"}}], "num_found": 1}

    cbcsdk_mock.mock_request('POST', "/api/alerts/v7/orgs/test/alerts/_search", on_post)
    api = cbcsdk_mock.api
    # no assertions, the check is that the post request is formed correctly.
    query = api.select(BaseAlert).set_workload_kinds(["123"]).set_rows(1)
    len(query)
