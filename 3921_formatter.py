"""Generate the ASCII file required for form 3921 transmission to the IRS"""
import yaml
import argparse

def parse_args():
    """Parse the command line arguments"""
    parser = argparse.ArgumentParser(
            prog="3921_formatter",
            description = "Outputs a file suitable for upload to IRS FIRE system for 3921 forms")
    parser.add_argument("input_file", help="The file with information on the ISO transaction")
    parser.add_argument("output_file", help="The output file")
    parser.add_argument("--config_file",
                        default="config.yaml",
                        help="The file specifying the output file format. default: config.yaml")
    return parser.parse_args()

def parse_file(filename):
    """Parse a yaml file"""
    with open(filename, 'r') as file:
        contents = yaml.safe_load(file) 
    return contents

def output_ascii_file(filename, contents):
    """Write out the ASCII file for IRS"""
    contents_ascii = contents.encode('ascii')
    with open(filename, 'wb') as f:
        f.write(contents_ascii)

def standardize_amounts(pay_str):
    """standardize money amounts to format requirements"""
    if "." in pay_str:
        pay = pay_str.split(".")
        assert len(pay) == 2
        if len(pay[1]) > 2:
            pay[1] = pay[1][:2] # clip decimal positions beyond cents
        pay = "".join(pay) + "0"*(2-len(pay[1])) # standardize to cents
    else: # no decimal, add 00 for cents
        pay = pay_str + "00"
    return pay

def build_record(contents, record_spec):
    """Build the a record according to specification and contents"""
    rec = ""
    for field_name in record_spec:
        field_spec = record_spec[field_name]
        if "Value" in field_spec:
            val = str(field_spec["Value"])
        elif "Key" in field_spec:
            content_key = field_spec["Key"]
            if "Required" in field_spec and field_spec["Required"]==1:
                if content_key not in contents:
                    assert False, 'Required field "{}" not found in input file'.format(content_key)
            val = str(contents[content_key]) if content_key in contents else None
        else:
            val = None

        if "Payment" in field_spec and field_spec["Payment"]==1:
            val = standardize_amounts(val)

        justify = "Left" if "Justify" not in field_spec else field_spec["Justify"]
        field_len = field_spec["Length"]
        fill_char = field_spec["Fill"] if "Fill" in field_spec else " "
        if val is not None:
            # clip value to length of field
            if len(val) > field_len:
                val = val[:field_len]

            # build field
            if justify == "Left":
                field = val + fill_char*(field_len-len(val))
            elif justify == "Right":
                field = fill_char*(field_len-len(val)) + val
        else:
            field = fill_char*field_len
        rec += field
    return rec

def build_file(contents, config):
    """Iterate through the records to build the file"""
    ascii_rep = ""
    for record_name in config:
        ascii_rep += build_record(contents, config[record_name])
    return ascii_rep

if __name__ == "__main__":
    args = parse_args()
    contents = parse_file(args.input_file)
    config = parse_file(args.config_file)
    ascii_rep = build_file(contents, config)
    output_ascii_file(args.output_file, ascii_rep)
