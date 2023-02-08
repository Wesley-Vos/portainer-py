import base64
import collections
import json
import os
import os.path
import shlex
import string
from datetime import datetime
from packaging.version import Version

def compare_version(v1, v2):
    """Compare docker versions

    >>> v1 = '1.9'
    >>> v2 = '1.10'
    >>> compare_version(v1, v2)
    1
    >>> compare_version(v2, v1)
    -1
    >>> compare_version(v2, v2)
    0
    """
    s1 = Version(v1)
    s2 = Version(v2)
    if s1 == s2:
        return 0
    elif s1 > s2:
        return -1
    else:
        return 1


def version_lt(v1, v2):
    return compare_version(v1, v2) > 0


def convert_filters(filters):
    result = {}
    for k, v in iter(filters.items()):
        if isinstance(v, bool):
            v = 'true' if v else 'false'
        if not isinstance(v, list):
            v = [v, ]
        result[k] = [
            str(item) if not isinstance(item, str) else item
            for item in v
        ]
    return json.dumps(result)


