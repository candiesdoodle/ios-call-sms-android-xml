import csv
import xml.etree.ElementTree as ET
import argparse
import os
import datetime

def indent(elem, level=0):
    """Pretty-prints XML (in-place)."""
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

def csv_to_xml_calls(csv_file, xml_file):
    """Converts a CSV file of call logs to XML."""

    if not os.path.exists(csv_file):
        print(f"Error: CSV file '{csv_file}' not found.")
        return

    try:
        with open(csv_file, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            call_logs = list(reader)
    except FileNotFoundError:
        print(f"Error: CSV file '{csv_file}' not found.")
        return
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return

    if not call_logs:
        print("CSV file is empty. No XML generated.")
        return

    root = ET.Element("calls")
    root.set("count", str(len(call_logs)))

    for log in call_logs:
        call = ET.SubElement(root, "call")

        # Set attributes, handling potential missing values and type conversions
        call.set("number", str(log.get("phone_number", "")))
        call.set("duration", str(log.get("duration", "0")))  # duration is already an int
        call.set("date", str(log.get("date", "0"))) # date is already correct
        call.set("type", str(log.get("type", "0"))) #type
        call.set("presentation", str(log.get("presentation", "1")))  # Default 1
        call.set("subscription_id", str(log.get("subscription_id", "null"))) #can be null
        call.set("post_dial_digits", str(log.get("post_dial_digits", "")))
        call.set("subscription_component_name", str(log.get("subscription_component_name", "null"))) #can be null
        call.set("readable_date", str(log.get("readable_date", "")))  # Should already be formatted
        call.set("contact_name", str(log.get("contact_name", "(Unknown)")))


    tree = ET.ElementTree(root)
    try:
        indent(root)  # Pretty-print
        tree.write(xml_file, encoding="utf-8", xml_declaration=True)
        print(f"Successfully converted '{csv_file}' to '{xml_file}'")
    except Exception as e:
        print(f"Error writing XML to '{xml_file}': {e}")

def main():
    parser = argparse.ArgumentParser(description="Convert a CSV file of call logs to XML.")
    parser.add_argument("csv_file", help="Path to the input CSV file")
    parser.add_argument("-o", "--output", default="call_logs.xml", help="Output XML file name (default: call_logs.xml)")

    args = parser.parse_args()
    csv_to_xml_calls(args.csv_file, args.output)

if __name__ == "__main__":
    main()
