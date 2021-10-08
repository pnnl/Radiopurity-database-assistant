import json
from pymongo import MongoClient


def extract_data(input_file):
    """
    This function extracts the header information and measurement data from the data file. It generally moves
    downwards in the file finding header information first.
    :param input_file: This argument is the file that was passed either from the interface drag&drop, or via
    a manually entered file path
    :return: Returns lines_list: a list of the lines with relavent information, measurement_fields: the data fields
    extracted from the data table, and num_header_items, which is the number of lines in lines_list corresponding to
    header information
    """

    print("type:", input_file.__class__)
    lines = input_file.readlines()
    lines_list = []
    adding_headers, adding_values, corrected_values = False, False, False
    num_header_items = -1  # Later reassigned not incremented, so this would be used to identify an error
    for line in lines:
        if adding_headers:
            if len(line) > 0 and line != "\n":
                lines_list.append({line.split(":")[0].split('.')[-1].strip(): line.split(":")[1].strip()})
            else:
                lines_list.append({"Sample area (cm2)": extract_sample_area(lines)})
                num_header_items = len(lines_list)
                adding_headers = False
        if "CONFLUENCE" in line:
            adding_headers = True
        if 'corrected' in line and 'Uncorrected' not in line:
            corrected_values = True
        if adding_values:
            if "|" in line:
                lines_list.append(line.strip())
            else:
                return lines_list, measurement_fields, num_header_items
        if "Energy Range" in line and corrected_values:
            measurement_fields = line.split("^")[1:]  # The first item would be empty, ""
            adding_values = True


def extract_sample_area(lines):
    """
    This function extracts the sample area used for the specific measurement. It is understood to be written in the
    line immediately following the line containing "Input command:". Here the area is given in decimal value after
    the two file paths in the input command
    :param lines: lines contains
    :return: Returns the measurement sample area as extracted from the input command line of the data file
    """
    active_line = False  # the active_line is the line below "Input command" that contains the sample area
    for line in lines:
        if active_line:
            sample_area = line.split(' ')[2]  # extracting the value after the two file paths in input command
            return sample_area
        if "Input command" in line:
            active_line = True
    return ""  # Empty string returned if the value is not given


def header_lines_to_json(header_lines):
    """
    This function converts the extracted lines with header information to a dictionary, and adds required fields
    if they were not in the data file
    :param header_lines: The extracted lines from the data file
    :return: Returns the dictionary with the measurement header information
    """
    dictionary = {}
    for header_line in header_lines:
        print(header_line)
        dictionary.update(header_line)
    required_fields = ['Sample', 'Date', 'Vendor', 'Experiment', 'Sample material',
                       'Readout mode', 'Purge time', 'Acquisition time', 'parent_id']
    for field in required_fields:
        if field not in dictionary:
            dictionary.update({field: ""})
    return dictionary


def values_lines_to_json(lines, fields):
    """
    This function converts the extracted lines of the uncorrected data table in the data file and converts them
    to a dictionary, such that they could be inserted into a MongoDB collection
    :param lines: The extracted lines from the data file
    :param fields: The data fields in the table, e.g. Alpha Counts, Total Emissivity, etc.
    :return: Returns the dictionary, where each energy range contains a dictionary with each measurement value
    """
    ranges_dictionary = {}
    for line in lines:
        values = line.split("|")[1:len(fields)]  # the last 2 items would be blank as the lines start and end with "|"
        within_range_dict = {}
        for i in range(1, len(fields)-1):  # the last item in fields is '\n, and the first is "Energy Range"
            dict_ = {fields[i].strip(): values[i]}
            within_range_dict.update(dict_)
        ranges_dictionary.update({values[0].replace('.', ','): within_range_dict})
    energy_range_dict = {"Energy Range (MeV)": ranges_dictionary}
    return energy_range_dict


def combine_sections(headers, values):
    json_file = {'_version': 1}
    json_file.update(headers)
    json_file.update(values)
    return json_file


def write_to_output_file(json_file, file_path):
    if file_path is not None:
        output_file_path = file_path[0:file_path.find('.')] + "_JSONConversion.json"
        json_str = json.dumps(json_file, indent=4)
        with open(output_file_path, 'w') as output_file:
            output_file.write(json_str)


def insert_json_to_collection(json_file):
    # This function inserts the formatted JSON file (held as a dictionary) into the MongoDB collection given below
    client = MongoClient("172.17.0.5", 27017)
    db = client["xia_pytest_data"]
    coll = db.assays
    inserting = coll.insert_one(json_file)
    read_file = coll.find_one(json_file)
    return str(read_file['_id'])


def conversion_main(data_file, file_path=None):
    """
    This is the main function of the module, from which all major functions are called resulting in a final formatted
    and inserted JSON file by calling this function from another module and passing the file content as an argument
    :param data_file: This is the file entered by the user to be converted and inserted
    :param file_path: Optional: if the file user wants to save the converted JSON file, it will be in the same directory
    """
    lines_str, table_fields, header_items_count = extract_data(data_file)
    _json_file_headers = header_lines_to_json(lines_str[:header_items_count])
    _json_file_values = values_lines_to_json(lines_str[header_items_count:], table_fields)
    _json_file = combine_sections(_json_file_headers, _json_file_values)
    print("Final type:", type(_json_file))
    print(_json_file["Energy Range (MeV)"])
    # write_to_output_file(_json_file, file_path)
    _id = insert_json_to_collection(_json_file)
    return "The data from ____ was uploaded to the database.", "_id: " + _id


if __name__ == "__main__":
    # This is for direct use/testing of the module, requiring the filepath of the data file
    filepath = "file/path/of/data/file/data_file.txt"  # Enter manually here if running module alone
    _input_file = open(filepath, 'r')
    conversion_main(_input_file, filepath)
