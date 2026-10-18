from json import *
import os
def id_priority_cargo(call_id = str()):
    call_id = call_id.lower().strip()
    with open(f"harborflow_02\dataset\manifests\{call_id}.json", "r") as file:
        print(file.read())

if __name__ == "__main__":
    test_call_id = "HFL-AAR-2071"
    # id_priority_cargo(test_call_id)
    dict = {}

    dict["Fireifwork"] = 1
    print(dict)