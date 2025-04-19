import sqlite3
import datetime
import argparse
import csv
import os
import pandas as pd  # Import pandas
import chardet
import re  # Import the regular expression module
import typedstream
import xml.etree.ElementTree as ET  # Import ElementTree

def convert_datetime(date):
    date_java = 0
    date_readable = "Invalid Date"
    try:
        mod_date = datetime.datetime(2001, 1, 1, tzinfo=datetime.timezone.utc)
        unix_timestamp = int(mod_date.timestamp()) * 1000000000
        new_date = int((date + unix_timestamp) / 1000000000)
        original_date_obj = datetime.datetime.fromtimestamp(new_date)
        date_java = int(original_date_obj.timestamp() * 1000)  # Correct Java TS
        date_readable = original_date_obj.strftime("%d %b %Y %l:%M:%S%p").replace("AM", "am").replace("PM","pm").replace("am"," am").replace("pm"," pm")
    except Exception as e:
        print(f"Error converting date for ROWID {rowid}: {e}")
        # Keep defaults: date_java = 0, date_readable = "Invalid Date"
    return date_java,date_readable



# date_string = '2001-01-01'
# mod_date = datetime.datetime.strptime(date_string, '%Y-%m-%d')



def read_messages(db_file):
    """
    Reads messages from an iMessage SQLite database file and returns them.

    Args:
        db_file (str): Path to the SQLite database file.
        n (int):  Number of most recent messages to retrieve.  If None, retrieve all.
        self_number (str):  Identifier for self messages (default: 'Me').
        human_readable_date (bool): Convert dates to human-readable format (default: True).

    Returns:
        list: A list of dictionaries, where each dictionary represents a message.
              Returns an empty list if the database file does not exist or if any error occurs.
    """
    elf_number = 'Me'
    if not os.path.exists(db_file):
        print(f"Error: Database file '{db_file}' not found.")
        return []

    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        query = """
        SELECT message.ROWID, message.date, message.text, message.attributedBody, handle.id, message.is_from_me, message.cache_roomnames, message.service
        FROM message
        LEFT JOIN handle ON message.handle_id = handle.ROWID
        """
        # if n is not None:
        #     query += f" ORDER BY message.date DESC LIMIT {n}"  # Initial sort by date DESC for -n option

        results = cursor.execute(query).fetchall()
        messages = []

        for result in results:
            rowid, date, text, attributed_body, handle_id, is_from_me, cache_roomname, service = result

            # --- Determine phone_number (handling sent messages differently) ---
            if is_from_me == 1 and handle_id is None:  # Sent message
                try:
                    # 1. Get chat_id from chat_message_join
                    chat_id_query = "SELECT chat_id FROM chat_message_join WHERE message_id = ?"
                    cursor.execute(chat_id_query, (rowid,))
                    chat_id_result = cursor.fetchone()

                    if chat_id_result:
                        chat_id = chat_id_result[0]

                        # 2. Get chat_identifier from chat
                        chat_identifier_query = "SELECT chat_identifier FROM chat WHERE ROWID = ?"
                        cursor.execute(chat_identifier_query, (chat_id,))
                        chat_identifier_result = cursor.fetchone()

                        if chat_identifier_result:
                            phone_number = str(chat_identifier_result[0])
                        else:
                            phone_number = self_number # Default if no chat_identifier found
                    else:
                        phone_number = self_number   # Default if no chat_id found
                except sqlite3.Error as e:
                    print(f"Error getting chat_identifier for ROWID {rowid}: {e}")
                    phone_number = self_number  # Fallback in case of error
            else:
                phone_number = str("Not found" if (handle_id is None) else handle_id)
            # Ensure phone_number is always a string:
            #phone_number = str(self_number if (handle_id is None or is_from_me == 1) else handle_id)
            phone_number = re.sub(r'\(.*?\)', '', phone_number).strip()
            if phone_number.startswith("+91") and len(phone_number) < 13:
                phone_number = phone_number[3:]  # Strip "+91"
            # if (phone_number==self_number and attributed_body is not None):
            # if (rowid==18661 and attributed_body is not None):
            #
            # #     print(f"ROWID: {rowid}, Attributed Body (decoded): {attributed_body.decode(encoding, errors='replace')}")
            #     input("Press")

            body = None  # Initialize body
            if text is not None:
                body = text
            elif attributed_body is not None:
                try:
                    body = typedstream.unarchive_from_data(attributed_body).contents[0].value.value
                    # print(f"{rowid}, {temp.contents[0].value.value}")
                    # attributed_body = attributed_body.decode('utf-8', errors='replace')
                    #
                    # #  more robust extraction using find and slicing:
                    # start = attributed_body.find("NSString") + len("NSString")
                    # end = attributed_body.find("NSDictionary")
                    # if start > len("NSString") - 1 and end > -1:  # Check if both markers were found
                    #     body = attributed_body[start:end].strip()[6:-12]  # proper body extraction
                    # else:
                    #     body = ""  # set body to empty if markers are not present

                except Exception as e:
                    print(f"Error decoding attributedBody for ROWID {rowid}: {e}")
                    continue  # skip this message
            else:
                continue  # Skip if both text and attributed_body are None


            date_java,date_readable=convert_datetime(date)

            messages.append({
                "rowid": rowid,
                "date": date_java,
                "readable_date": date_readable,
                "body": body,
                "phone_number": phone_number,  # Now always a string
                "is_from_me": is_from_me,
                "cache_roomname": cache_roomname,
                "service": service  # Add the service column
            })

        conn.close()
        return messages

    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return []


def get_cutoff_from_xml(xml_file):
    """Extracts the latest 'date' attribute from 'sms' elements in an XML file."""
    if not os.path.exists(xml_file):
        print(f"Error: XML file '{xml_file}' not found.")
        return -1

    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        latest_timestamp = -1

        # Iterate through all 'sms' elements (using XPath for conciseness)
        for sms in root.findall(".//sms"):  # Find all 'sms' elements anywhere in the tree
            date_str = sms.get("date")
            if date_str:
                try:
                    date_timestamp = int(date_str)
                    latest_timestamp = max(latest_timestamp, date_timestamp)
                except ValueError:
                    print(f"Warning: Invalid date attribute found in XML: {date_str}")
                    # Continue processing other elements even if one is invalid
        if latest_timestamp ==-1:
          return -1 #return default if no sms tag is present
        dt_object = datetime.datetime.fromtimestamp(latest_timestamp / 1000)
        formatted_date = dt_object.strftime("%d %b %Y %l:%M:%S%p").replace("AM", "am").replace("PM", "pm").replace("am"," am").replace("pm", " pm")
        print(f"Taking the cutoff as: {latest_timestamp}, i.e: {formatted_date}")
        return latest_timestamp
    except ET.ParseError:
        print(f"Error: Could not parse XML file '{xml_file}'.")
        return -1  # Return -1 to indicate an error (and write all rows)
    except Exception as e:
        print(f"An unexpected error occurred while processing the XML file: {e}")
        return -1


def write_to_csv(messages, output_file,xml_file=None):
    """Writes the extracted messages to a CSV file, sorted by date.

    Args:
        messages (list): List of message dictionaries.
        output_file (str): Path to the output CSV file.
    """
    if not messages:
        print("No messages to write.")
        return

    try:
        # Convert the list of dictionaries to a Pandas DataFrame
        df = pd.DataFrame(messages)
        # 1. Sort by 'service' so 'SMS' comes last (we'll keep the last duplicate)
        df = df.sort_values(by=['date', 'body', 'phone_number', 'is_from_me', 'service'],
                            ascending=[True, True, True, True, False])
        # 2. Drop duplicates, keeping the last occurrence (which will be 'SMS' if present)
        df.drop_duplicates(subset=['date', 'body', 'phone_number', 'is_from_me'], keep='last', inplace=True)
        # --- Sort by 'date' (the raw numeric timestamp) ---
        df = df.sort_values(by='date')




        # sort by date again
        df = df.sort_values(by='date')
        if xml_file:
            cutoff_timestamp = round(int(get_cutoff_from_xml(xml_file))/1000)*1000
            if cutoff_timestamp == -1:
                print("Using default behavior (writing all rows) due to XML error.")
        else:
            while True:
                try:
                    user_input = input(
                        "Input the last Java timestamp in the existing database on the phone (or press Enter to write all rows): ").strip()
                    if user_input == "":
                        cutoff_timestamp = -1  # Write all rows
                        break
                    else:
                        cutoff_timestamp = round(int(user_input) / 1000)*1000
                        break# Convert to milliseconds                    break  # Exit loop if input is valid
                except ValueError:
                    print("Invalid input. Please enter a numeric timestamp or press Enter.")

        total_rows = len(df)
        if cutoff_timestamp != -1:
            df_filtered = df[df['date'] > cutoff_timestamp]
        else:
            df_filtered = df
        rows_written = len(df_filtered)
        rows_not_written = total_rows - rows_written

        # Write the DataFrame to CSV
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['rowid', 'date',  'readable_date', 'body', 'phone_number', 'is_from_me', 'cache_roomname', 'service']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            # Convert DataFrame back to a list of dictionaries for writing
            writer.writerows(df_filtered.to_dict('records'))
        print(f"Messages successfully written to {output_file}, deduplicated, sorted, and filtered.")
        print(f"Total rows: {total_rows}")
        print(f"Rows written: {rows_written}")
        print(f"Rows not written: {rows_not_written}")

    except IOError as e:
        print(f"I/O error writing to CSV: {e}")
    except Exception as e:
        print(f"An unexpected error occurred while writing to CSV: {e}")


def main():
    parser = argparse.ArgumentParser(description="Extract iMessage data and save to CSV.")
    parser.add_argument("db_file", help="Path to the SQLite database file")
    # parser.add_argument("-n", type=int, default=None, help="Number of recent messages (default: all)")
    parser.add_argument("-o", "--output", default="messages", help="Output CSV filename without extenstion (default: messages)")
    # parser.add_argument("-s", "--self", default="Me", help="Identifier for self messages (default: Me)")
    # parser.add_argument("-r", "--raw_date", action="store_false", help="Use raw date format")
    parser.add_argument("-x", "--xml", help="Path to the XML file for timestamp filtering",default=None)  # Added XML argument

    args = parser.parse_args()

    messages = read_messages(args.db_file)

    if messages:
        write_to_csv(messages, f"{args.output}.csv", xml_file=args.xml)


if __name__ == "__main__":
    main()