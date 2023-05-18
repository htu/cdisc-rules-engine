import copy

def get_dataset_variables(metadata,domain_name, key, val):
    dataset_variables = []
    for dataset in metadata['datasets']:
        if dataset['name'] == domain_name:
            dataset_variables = dataset['datasetVariables']
            break

    class_variables = []
    for class_ in metadata['classes']:
        for var in class_['classVariables']:
            if var.get(key) == val:
                class_variables.append(var.get("name"))

    variable_names = []
    for variable in dataset_variables:
        variable_name = variable['name']
        if variable_name in class_variables:
            variable_names.append(variable_name)

    return variable_names


def get_dataset_component(datasets, dataset_name, var_list):
    dataset_component = None

    for dataset in datasets:
        if dataset['name'] == dataset_name:
            dataset_component = copy.deepcopy(dataset)
            break

    if dataset_component:
        dv = []
        dataset_variables = dataset_component.get('datasetVariables', [])
        for variable in dataset_variables:
            if variable.get("name") in var_list:
                dv.append(variable)
        dataset_component["datasetVariables"] = dv
    
    return dataset_component


def find_standard_objects(obj, domain: str = None, key: str = "role", val: str = None):
    v_prg = "find_objects"
    results = []
    if isinstance(obj, dict):
        dom = obj.get("_links", {}).get("self", {}).get("href")
        dm1 = f"/datasets/{domain}/"
        v1 = obj.get(key)
        echo_msg(v_prg, 1.111, f"{v1}={val},{dm1}={dom}?")
        if v1 == val and dm1 in dom:
            results.append(obj)
        for value in obj.values():
            results += find_standard_objects(value, domain, key, val)
    elif isinstance(obj, list):
        for item in obj:
            results += find_standard_objects(item, domain, key, val)
    return results


def get_ig(ifn: str = "./dist/sdtmig-3-4.json",
           domain: str = "AE", key: str = "role", val: str = "Timing"):
    with open(ifn) as f:
        # Load the JSON data into a Python object
        data = json.load(f)
    return find_standard_objects(data, domain, key, val)


def get_mdl(ifn: str = "./dist/sdtm-2-0.json",
            domain: str = "AE", key: str = "role", val: str = "Timing"):
    with open(ifn) as f:
        # Load the JSON data into a Python object
        data = json.load(f)
    return find_standard_objects(data, domain, key, val)


if __name__ == "__main__":
    data = {
        "datasets": [
            {
                "_links": {"parentClass": {"title": "Events"}},
                "name": "AE",
                "datasetVariables": [
                    {
                        "name": "USUBJID",
                        "ordinal": 2,
                    },
                    {
                        "name": "AESEQ",
                        "ordinal": 3,
                    },
                    {
                        "name": "AETERM",
                        "ordinal": 4,
                    },
                    {
                        "name": "VISITNUM",
                        "ordinal": 17,
                    },
                    {
                        "name": "VISIT",
                        "ordinal": 18,
                    },
                ],
            }
        ],
        "classes": [
            {
                "name": "Events",
                "label": "Events",
                "classVariables": [
                    {"name": "--TERM", "ordinal": 1},
                    {"name": "--SEQ", "ordinal": 2},
                ],
            },
            {
                "name": "GENERAL_OBSERVATIONS_CLASS",
                "label": "GENERAL_OBSERVATIONS_CLASS",
                "classVariables": [
                    {
                        "name": "STUDYID",
                        "role": "IDENTIFIER",
                        "ordinal": 1,
                    },
                    {
                        "name": "DOMAIN",
                        "role": "IDENTIFIER",
                        "ordinal": 2,
                    },
                    {
                        "name": "USUBJID",
                        "role": "IDENTIFIER",
                        "ordinal": 3,
                    },
                    {
                        "name": "AETERM",
                        "role": "IDENTIFIER",
                        "ordinal": 4,
                    },
                    {
                        "name": "VISITNUM",
                        "role": "TIMING",
                        "ordinal": 17,
                    },
                    {
                        "name": "VISIT",
                        "role": "TIMING",
                        "ordinal": 18
                    },
                    {
                        "name": "TIMING_VAR",
                        "role": "TIMING",
                        "ordinal": 33,
                    },
                ],
            },
        ],
    }

    key = "role"
    val = "TIMING"

    variable_names = get_dataset_variables(data, "AE", key, val)
    print(f"Find 1: {variable_names}")  # Output: ['VISITNUM', 'VISIT', 'TIMING_VAR']
    data_comp = get_dataset_component(data["datasets"],"AE", variable_names)
    print(f"{data_comp}\n") 

    variable_names = get_dataset_variables(data, "AE", key, "IDENTIFIER")
    print(f"Find 2: {variable_names}")  # Output: ['VISITNUM', 'VISIT', 'TIMING_VAR']
    data_comp = get_dataset_component(data["datasets"],"AE", variable_names)
    print(data_comp)  

    # Open the JSON file
    # https://github.com/cdisc-org/cdisc-library-src-files/blob/master/cdisc-json/products/data-tabulation/
    timing1_objs = get_mdl()
    timing2_objs = get_ig()
    # Access the data in the object
    # print(data.keys())

    