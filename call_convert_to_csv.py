import sqlite3
import datetime
import argparse
import csv
import os
import pandas as pd
import chardet
import re
import math

def convert_datetime(date):
    date_java = 0
    date_readable = "Invalid Date"
    try:
        mod_date = datetime.datetime(2001, 1, 1, tzinfo=datetime.timezone.utc)
        unix_timestamp = (mod_date.timestamp())
        new_date = ((date + unix_timestamp))
        original_date_obj = datetime.datetime.fromtimestamp(new_date)
        date_java = int(original_date_obj.timestamp())  # Correct Java TS
        date_readable = original_date_obj.strftime("%d %b %Y %l:%M:%S%p").replace("AM", "am").replace("PM",
                                                                                                      "pm").replace(
            "am",
            " am").replace(
            "pm", " pm")
        # print(f"{date}, {date_java}; {date_readable}")

    except Exception as e:
        print(f"Error converting date for ROWID {rowid}: {e}")
        # Keep defaults: date_java = 0, date_readable = "Invalid Date"
    return date_java*1000,date_readable

def read_call_logs(db_file, self_phone_number):
    """Reads call logs from an SQLite database file and returns them as a list of dictionaries."""

    if not os.path.exists(db_file):
        print(f"Error: Database file '{db_file}' not found.")
        return []

    try:
        conn = sqlite3.connect(db_file)
        conn.text_factory = str  # Ensure text handling
        cursor = conn.cursor()

        query = """
        SELECT ZCALLRECORD.Z_PK, ZCALLRECORD.ZADDRESS, ZCALLRECORD.ZDURATION, ZCALLRECORD.ZDATE,
               ZCALLRECORD.ZORIGINATED, ZCALLRECORD.ZANSWERED, ZCALLRECORD.ZDISCONNECTED_CAUSE,
               ZCALLRECORD.ZSERVICE_PROVIDER
        FROM ZCALLRECORD
        """
        # No JOIN needed in this case, as all required data is in ZCALLRECORD

        results = cursor.execute(query).fetchall()
        call_logs = []

        for result in results:
            rowid, address, duration, date, originated, answered, disconnected_cause, service_provider = result

            # --- Phone Number ---
            phone_number = str(address) if address else ""  # Handle potential None values

            # --- Duration ---
            duration = round(duration) if duration is not None else 0

            # --- Date Conversion and Handling ---
            date_java = 0
            date_readable = "Invalid Date"

            date_java,date_readable=convert_datetime(date)


            # --- Call Type and Type of Call ---
            if originated == 0:  # Incoming
                type_of_call = "Incoming"
                if answered == 0:
                    call_type = 3  # Missed
                else:
                    call_type = 1  # Incoming
            elif originated == 1: #outgoing
                type_of_call = "Outgoing"
                call_type = 2  # Outgoing
            else:  # Should not happen, but handle for robustness
                type_of_call = "Unknown"
                call_type = 0  # Unknown

            if disconnected_cause == 6:
                call_type = 5  # Rejected


            # --- subscription_id and subscription_component_name ---
            if service_provider and "whatsapp" in service_provider.lower():
                subscription_id = f"{self_phone_number}@s.whatsapp.net"
                subscription_component_name = "com.whatsapp/com.whatsapp.calling.telecom.SelfManagedConnectionService"
            else:
                subscription_id = "1"  # Default value
                subscription_component_name = "com.android.phone/com.android.services.telephony.TelephonyConnectionService"

            call_logs.append({
                "rowid": rowid,
                "phone_number": phone_number,
                "duration": duration,
                "date": date_java,
                "type": call_type,
                "type_of_call": type_of_call,
                "presentation": 1,  # Always 1
                "subscription_id": subscription_id,
                "post_dial_digits": "",  # Always empty
                "subscription_component_name": subscription_component_name,
                "readable_date": date_readable,
                "contact_name": "(Unknown)",  # Default value
                "service_provider" : service_provider
            })

        conn.close()
        return call_logs

    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return []

def write_to_csv(call_logs, output_file):
    if not call_logs:
        print("No call logs to write.")
        return

    try:
        df = pd.DataFrame(call_logs)

        # --- Sort by 'date' (ascending) ---
        df = df.sort_values(by='date')

        # --- Write to CSV ---
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['rowid', 'phone_number', 'duration', 'date', 'type', 'type_of_call',
                          'presentation', 'subscription_id', 'post_dial_digits',
                          'subscription_component_name', 'readable_date', 'contact_name', 'service_provider']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
            writer.writeheader()
            writer.writerows(df.to_dict('records'))

        print(f"Call logs successfully written to {output_file}, sorted by date.")

    except IOError as e:
        print(f"I/O error writing to CSV: {e}")
    except Exception as e:
        print(f"An unexpected error occurred while writing to CSV: {e}")

def main():
    parser = argparse.ArgumentParser(description="Extract call log data from an SQLite database and save to CSV.")
    parser.add_argument("db_file", help="Path to the SQLite database file")
    parser.add_argument("-o", "--output", default="call_logs.csv", help="Output CSV file name (default: call_logs.csv)")

    args = parser.parse_args()

    # Get self_phone_number from user input
    self_phone_number = input("Enter your phone number (for WhatsApp subscription ID): ").strip()

    call_logs = read_call_logs(args.db_file, self_phone_number)

    if call_logs:
        write_to_csv(call_logs, args.output)

if __name__ == "__main__":
    main()
