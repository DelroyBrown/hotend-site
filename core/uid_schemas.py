import re
from enum import Enum


class UIDSchema:
    def __init__(self, title, regex):
        self.regex = regex
        self.title = title

    def match(self, uid_code):
        return re.fullmatch(self.regex, uid_code)


class UID_SCHEMAS(Enum):
    # V6 barcodes are a 9-digit integer, zero-padded to the left.
    V6_BARCODE = UIDSchema("V6 Barcode", r"[0-9]{9}")

    # V7 serial numbers follow a DDMMYY-XXXX structure, where the Xs are capitalised alphanumeric.
    V7_SERIAL = UIDSchema("V7 Serial Number", r"[0-3][0-9][0-1][0-9][0-9][0-9]\-[0-9AC-HJ-NP-Z]{4}")

    # Hemera QR codes are YYMMDDXXXXX, where the Xs are numeric.
    HEMERA_QR = UIDSchema("Hemera QR Code", r"[0-9][0-9][0-1][0-9][0-3][0-9][0-9]{5}")

    # Revo Roto QR codes are 128-QQ-YYMMDD-XXXX, where the Qs are numeric for motor type and Xs are numeric.
    ROTO_QR = UIDSchema("Revo Roto QR Code", r"128-[0-9]{2}-[0-9][0-9][0-1][0-9][0-3][0-9]-[0-9]{4}")

    @classmethod
    def match_all(cls, uid_code):
        """Return a list of all schemas that match the given UID."""
        matched = []
        for schema_entry in cls:
            if schema_entry.value.match(uid_code):
                matched.append(schema_entry)
        return matched

    @classmethod
    def choices(cls):
        """Return a tuple of tuples, suitable for use in a Django ChoiceField."""
        return (
            (schema_entry.name, schema_entry.value.title)
            for schema_entry in cls
        )

    @classmethod
    def get_schema(cls, schema_entry_name):
        """
        Helper method. Convert the name of a schema entry into the actual UIDSchema object.
        Return None if the entry name doesn't exist on this enum.
        """
        for schema_entry in cls:
            if schema_entry.name == schema_entry_name:
                return schema_entry.value
        return None
