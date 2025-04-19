import csv
import xml.etree.ElementTree as ET
import argparse
import os
import datetime

def indent(elem, level=0):
    """
    In-place pretty-printing for XML.  This function is a workaround
    for the missing 'pretty_print' argument in some ElementTree versions.
    """
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

def csv_to_xml(csv_file, xml_file):
    """
    Converts a CSV file containing SMS data to an XML file conforming to a specific schema.

    Args:
        csv_file (str): Path to the input CSV file.
        xml_file (str): Path to the output XML file.
    """

    if not os.path.exists(csv_file):
        print(f"Error: CSV file '{csv_file}' not found.")
        return

    try:
        with open(csv_file, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            messages = list(reader)  # Read all rows into a list of dictionaries

    except FileNotFoundError:
        print(f"Error: CSV file '{csv_file}' not found.")
        return
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return

    if not messages:
        print("CSV file is empty. No XML generated.")
        return

    root = ET.Element("smses")
    root.set("count", str(len(messages)))

    for msg in messages:
        sms = ET.SubElement(root, "sms")

        # Required attributes with defaults if missing:
        sms.set("address", msg.get("phone_number", ""))
        # # Convert readable date back to Java timestamp if possible, else use 0
        # try:
        #    date_obj = datetime.datetime.strptime(msg.get("date", ""), "%Y-%m-%d %H:%M:%S")
        #    java_timestamp = int(date_obj.timestamp() * 1000)
        # except:
        #     try:
        #       #try java time stamp format
        #       java_timestamp = int(msg.get("date","0"))
        #     except:
        #       java_timestamp = 0  # Default if conversion fails
        # sms.set("date", str(java_timestamp))
        sms.set("date", msg.get("date", ""))
        sms.set("body", msg.get("body", ""))
        sms.set("type", "1" if msg.get("is_from_me") == '0' else "2") # csv stores as str not int
        sms.set("read", "1" if msg.get("is_from_me") == '0' else "0") # Assuming from_me = 0 is read
        sms.set("status", "-1")

        # Optional attributes (set to "null" as per the example XML):
        sms.set("protocol", "0")
        sms.set("subject", "null")
        sms.set("toa", "null")
        sms.set("sc_toa", "null")
        sms.set("service_center", "null")
        sms.set("locked", "0")
        # Use readable date if available, otherwise set to "null":
        sms.set("readable_date", msg.get("readable_date", "null"))
        sms.set("contact_name", "(Unknown)")  # Default value
        sms.set("date_sent", "0")
        sms.set("sub_id", "-1")  # Add sub_id attribute
        
    tree = ET.ElementTree(root)
    try:
        indent(root)  # Apply pretty-printing
        tree.write(xml_file, encoding="utf-8", xml_declaration=True) # removed pretty_print
        print(f"Successfully converted '{csv_file}' to '{xml_file}'")
    except Exception as e:
        print(f"Error writing XML to '{xml_file}': {e}")

def main():
    parser = argparse.ArgumentParser(description="Convert a CSV file of SMS messages to XML.")
    parser.add_argument("csv_file", help="Path to the input CSV file")
    parser.add_argument("-o", "--output", default="output.xml", help="Output XML file name (default: output.xml)")

    args = parser.parse_args()
    csv_to_xml(args.csv_file, args.output)

if __name__ == "__main__":
    main()