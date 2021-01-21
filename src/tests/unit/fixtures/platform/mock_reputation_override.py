"""Mock responses for Reputation Override queries."""


REPUTATION_OVERRIDE_SHA256_REQUEST = {
    "description": "An override for a sha256 hash",
    "override_list": "BLACK_LIST",
    "override_type": "SHA256",
    "sha256_hash": "af62e6b3d475879c4234fe7bd8ba67ff6544ce6510131a069aaac75aa92aee7a",
    "filename": "foo.exe"
}

REPUTATION_OVERRIDE_SHA256_RESPONSE = {
    "id": "e9410b754ea011ebbfd0db2585a41b07",
    "created_by": "example@example.com",
    "create_time": "2021-01-04T15:24:18.002Z",
    "description": "An override for a foo.exe",
    "override_list": "BLACK_LIST",
    "override_type": "SHA256",
    "sha256_hash": "af62e6b3d475879c4234fe7bd8ba67ff6544ce6510131a069aaac75aa92aee7a",
    "filename": "foo.exe"
}

REPUTATION_OVERRIDE_SHA256_SEARCH_RESPONSE = {
    "num_found": 1,
    "results": [
        {
            "id": "e9410b754ea011ebbfd0db2585a41b07",
            "created_by": "example@example.com",
            "create_time": "2021-01-04T15:24:18.002Z",
            "description": "An override for a foo.exe",
            "override_list": "BLACK_LIST",
            "override_type": "SHA256",
            "sha256_hash": "af62e6b3d475879c4234fe7bd8ba67ff6544ce6510131a069aaac75aa92aee7a",
            "filename": "foo.exe"
        }
    ]
}
