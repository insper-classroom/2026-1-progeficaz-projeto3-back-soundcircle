import re
from bson import ObjectId
from bson.json_util import dumps


def sanitize_text(text):
    if not isinstance(text, str):
        return ""
    return re.sub(r"\s+", " ", text.strip())


class JSONEncoder:
    @staticmethod
    def encode(obj):
        return dumps(obj)
