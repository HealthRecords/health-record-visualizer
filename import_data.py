# This file imports data from provided XML files into sqlite.
# If you want to control the files used, run the two scripts we call directly.
import sys

import preprocess_apple_health
import preprocess_cda


def main():
    print(F"Importing cda data from {preprocess_cda.get_default_cda_path()}")
    preprocess_cda.process_cda_file_with_cleanup(preprocess_cda.get_default_cda_path(), preprocess_cda.get_db_file_path())

    apple_xml_path = preprocess_apple_health.get_default_source_path()
    if not apple_xml_path.exists():
        print(f"Error: Apple XML file not found: {apple_xml_path}")
        sys.exit(10)
    print(F"Importing apple health data from {apple_xml_path}")
    apple_db_path = preprocess_apple_health.get_default_db_path()
    success = preprocess_apple_health.process_xml_file(apple_xml_path, apple_db_path)
    if not success:
        sys.exit(11)


if __name__ == "__main__":
    main()
