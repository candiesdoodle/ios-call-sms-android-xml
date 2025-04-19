# ios-call-sms-to-android-xml
Migrate IOS call history and SMS to Android without resetting Android
# iOS to Android Call/SMS Backup Converter

These Python scripts help you convert call logs and SMS/iMessage history from an unencrypted iOS backup into an XML format compatible with the [SMS Backup & Restore](https://play.google.com/store/apps/details?id=com.riteshsahu.SMSBackupRestore) app on Android. This allows you to merge your iOS history with your Android history.

**Disclaimer:** These scripts process your personal call and message backups. Handle your backup files (`.sqlite`, `.csv`, `.xml`) securely and be aware that they contain sensitive information. Use these scripts at your own risk.

## Prerequisites

1.  **Python 3:** Ensure you have Python 3 installed.
2.  **Required Libraries:** Install the necessary Python libraries using pip:
    ```bash
    pip install pandas chardet typedstream
    ```
3.  **Unencrypted iOS Backup:** You need an unencrypted backup of your iOS device (created via Finder/iTunes or extracted using third-party tools). Encrypted backups will not work.

    Refer https://github.com/candiesdoodle/ios_unencrypted_backup_extract_files and https://github.com/jsharkey13/iphone_backup_decrypt to obtain unencrypted extracts of SMS and call history.
    
5.  **iOS Backup Files:** Locate the following files within your unencrypted backup:
    *   **Call Logs:** Typically found at `HomeDomain/Library/CallHistoryDB/CallHistory.storedata` or potentially named `call_history.sqlite` (the scripts expect the latter based on usage examples, ensure you have the correct SQLite file).
    *   **SMS/iMessages:** Typically found at `HomeDomain/Library/SMS/sms.db`.
6.  **(For SMS/iMessage): Android Backup:** An existing XML backup file created by the "SMS Backup & Restore" app on your Android device. This is used to prevent importing messages you already have on the Android phone.

## Workflow & Usage

There are separate workflows for Call Logs and SMS/iMessages.

### A. Call Log Conversion

This process converts your iOS call history directly to an XML file for restoration. Android's call log usually handles duplicates automatically during restore.

**Steps:**

1.  **Convert iOS DB to CSV:** Run `call_convert_to_csv.py`, providing the path to your iOS call log database file.
    *   You will be prompted to enter your own phone number. This is used to correctly format the identifier for WhatsApp calls if detected.
    ```bash
    python call_convert_to_csv.py <path_to_ios_call_history.sqlite> [-o <output_csv_file>]
    ```
    Note: <path_to_ios_call_history.sqlite> can any file and extension and depends on how you extracted and named it.
    
    *   **Example:**
        ```bash
        # This will create call_logs.csv in the current directory
        python call_convert_to_csv.py ../ios_backup_location/decrypted_backup_location/call_history.sqlite
        Enter your phone number (for WhatsApp subscription ID): +11234567890
        ```
    *   The default output CSV is `call_logs.csv`. Use the `-o` flag to specify a different name.

3.  **Convert CSV to XML:** Run `calls_csv_to_xml.py`, providing the CSV file generated in the previous step.
    ```bash
    python calls_csv_to_xml.py <input_csv_file> [-o <output_xml_file>]
    ```
    *   **Example:**
        ```bash
        # This will create call_logs.xml from call_logs.csv
        python calls_csv_to_xml.py call_logs.csv -o call_logs.xml
        ```
    *   The default output XML is `call_logs.xml`. Use the `-o` flag to specify a different name.

4.  **Restore on Android:** Transfer the generated XML file (e.g., `call_logs.xml`) to your Android device and use the "SMS Backup & Restore" app to restore **Call Logs** from this file.

### B. SMS/iMessage Conversion

This process was designed to convert only the iOS messages that are *newer* than the latest message in an existing Android XML backup. This prevents duplicates. The script can be made to exectue and convert _all_ messages. but if you have thousands or tens of thousands of messages, restoring those may be painfully slow.

**Important Notes:**

*   **MMS:** This script primarily focuses on SMS and iMessage text content. MMS (media attachments) are not explicitly processed or included in the XML.
*   **Group Chats:** Not converted
*   **Deduplication:** The script attempts to deduplicate messages if both an iMessage and SMS version exist for the exact same message (same timestamp, body, sender/receiver), keeping the SMS version.

**Steps:**

1.  **Create Android Backup:** Use the "SMS Backup & Restore" app on your Android phone to create an XML backup of your current messages. Transfer this XML file to the same computer/directory where you are running the scripts.
2.  **Convert iOS DB to CSV (Filtered):** Run `sms_convert_to_csv.py`, providing the path to your iOS `sms.db` file **and** the path to the Android XML backup file using the `-x` flag.
    ```bash
    python sms_convert_to_csv.py <path_to_ios_sms.db> -x <android_backup.xml> [-o <output_csv_name_without_extension>]
    ```
    Note: <path_to_ios_sms.db> can any file and extension and depends on how you extracted and named it.
    
    *   **Example:**
        ```bash
        # This reads sms.db, checks against sms_android_backup.xml,
        # and creates messages.csv containing only newer iOS messages.
        python sms_convert_to_csv.py ../ios_backup_location/decrypted_backup_location/sms.db -x sms_android_backup.xml -o messages
        ```
    *   The script will read the latest message timestamp from the provided XML (`-x` flag) and only include messages from the iOS `sms.db` that are newer than that timestamp in the output CSV.
    *   The default output CSV is `messages.csv`. Use the `-o` flag to specify a different base name (e.g., `-o new_sms` creates `new_sms.csv`).
    *   **Alternative (Manual Timestamp):** If you don't provide the `-x` flag, the script will prompt you to manually enter the Java timestamp (in milliseconds) of the last message on your Android phone. Enter the timestamp or press Enter to include *all* messages (not recommended if you want to avoid duplicates).

4.  **Convert Filtered CSV to XML:** Run `sms_csv_to_xml.py`, providing the filtered CSV file generated in the previous step.
    ```bash
    python sms_csv_to_xml.py <filtered_input_csv_file> [-o <output_xml_file>]
    ```
    *   **Example:**
        ```bash
        # This will create output.xml from messages.csv
        python sms_csv_to_xml.py messages.csv -o sms_ios_incremental.xml
        ```
    *   The default output XML is `output.xml`. Use the `-o` flag to specify a different name (e.g., `sms_ios_incremental.xml`).

5.  **Restore on Android:** Transfer the generated XML file (e.g., `sms_ios_incremental.xml`) to your Android device and use the "SMS Backup & Restore" app to restore **Messages** from this file. Since this XML only contains newer messages, it should merge cleanly with your existing Android messages without creating duplicates handled by the script's timestamp filter.

## Contributing

Feel free to report issues or suggest improvements via GitHub Issues or Pull Requests.
