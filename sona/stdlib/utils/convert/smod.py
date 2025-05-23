class Convert:
    def to_str(self, value):
        return str(value)

    def to_float(self, value):
        try:
            return float(value)
        except:
            return None

    def to_int(self, value):
        try:
            return int(float(value))
        except:
            return None

convert = Convert()
import os
if os.environ.get("SONA_DEBUG") == "1" and os.environ.get("SONA_MODULE_SILENT") != "1":
    print("[DEBUG] convert module loaded")
