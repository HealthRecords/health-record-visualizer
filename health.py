"""
This is a command line interface to health_lib.py

Design note: This is an exploration tool, not a product. As I don't have documentation for the file formats,
I try to put assertions in, to verify my assumptions, like "A referenceRange only has one value". That's the only case
I have seen, but there are probably millions of cases I have not seen, yet. It's better to hit an assertion and fix
it, than to silently hide information.
"""
import glob
import json
from io import StringIO
from pathlib import Path
from typing import NoReturn, Iterable
import argparse
from datetime import datetime
import csv

# TODO Split this file into UI code, and library code. We already have text_ui, and xml_reader which use this file.
#       Should be able to pass in an output function (print, plot with matplotlib, generate html page, etc.
# TODO print_condition and print_medicines should be generalized and combined.
# TODO Do we want to have an option to process multiple or all stats in one run?
# TODO Should be able to graph anything with a value quantity and a date. This is only observations, at least
#      in my data. Need to handle string values for Observations
# TODO When getting multiple stats, I reread ALL the observation files for each stat. Optimize.
# TODO I don't currently handle the difference between < and <= on reference ranges. Is there really a difference?
# TODO New format for valueQuantity, see ValueQuantity doc string
# TODO Some data appears to be missing from my download (PSA).
# TODO Check single ended string referenceRanges, like "<50". How well does that graph? I treat this as
#       -sys.maxsize < X < 50
# TODO Not sure if do_vitals belongs here, or in health_lib or needs to be refactored.
# TODO Where does 'plot' belong? A third module, which s pluggable

from health_lib import StatInfo, Observation
from health_lib import  extract_all_values, yield_observation_files
from health_lib import list_categories, list_vitals, list_prefixes
from plot_health import plot


def print_conditions(cd: Path, csv_format: bool, match: str) -> NoReturn:
    path = cd / match
    conditions = []
    for p in glob.glob(str(path)):
        with open(p) as f:
            condition = json.load(f)
            conditions.append(
                (condition['resourceType'],
                 condition['recordedDate'],
                 condition['clinicalStatus']['coding'][0]['code'],
                 condition['verificationStatus']['coding'][0]['code'],
                 condition['code']['text'],
                 )
            )
    cs = sorted(conditions, key=lambda x: x[1])
    for condition in cs:
        if csv_format:
            print_csv(condition)
        else:
            # Almost the same as csv, but the csv version escapes special characters, if there are any.
            print(condition)

def print_procedures(cd: Path, csv_format: bool, match: str) -> NoReturn:
    path = cd / match
    conditions = []
    for p in glob.glob(str(path)):
        with open(p) as f:
            condition = json.load(f)
            conditions.append(
                (condition['resourceType'],
                 condition['performedDateTime'],
                 condition['status'],
                 condition['code']['text'],
                 )
            )
    cs = sorted(conditions, key=lambda x: x[1])
    for condition in cs:
        if csv_format:
            print_csv(condition)
        else:
            # Almost the same as csv, but the csv version escapes special characters, if there are any.
            print(condition)

def print_medicines(cd: Path, csv_format: bool, match: str, include_inactive: bool) -> NoReturn:
    path = cd / match
    conditions = []
    for p in glob.glob(str(path)):
        with open(p) as f:
            condition = json.load(f)
            is_active = not condition['status'] in ['completed', 'stopped']
            if is_active or include_inactive:
                d = condition['authoredOn']
                # Line up printed columns
                if len(d) == 10:
                    d += 10*' '
                conditions.append(
                    (condition['resourceType'],
                     d,
                     condition['status'],
                     condition['medicationReference']['display'],
                     )
                )
    cs = sorted(conditions, key=lambda x: x[1])
    for condition in cs:
        if csv_format:
            print_csv(condition)
        else:
            # Almost the same as csv, but the csv version escapes special characters, if there are any.
            print(condition)

def print_value(w: Observation):
    print(F"{w.name:10}: {w.date} - ", end="")
    values = w.data
    for value in values:
        print(F" {value.value:6.1f} {value.unit},", end="")
    print()


def print_csv(data: Iterable):
    output = StringIO()
    wr = csv.writer(output, quoting=csv.QUOTE_ALL)
    wr.writerow(data)
    print(output.getvalue(), end="")

def print_value_csv(w: Observation):
    fields = [w.name, w.date]
    values = w.data
    for value in values:
        fields.append(value.value)
        fields.append(value.unit)
        fields.append(value.name)
    print_csv(fields)

def print_values(ws: list[Observation], csv_format: bool) -> NoReturn:
    for w in ws:
        if csv_format:
            print_value_csv(w)
        else:
            print_value(w)


def print_vitals(observation_files: Iterable[str], category: str) -> NoReturn:
    vitals = list_vitals(observation_files, category)
    print(F"Files that have a category of '{category}' were found in files. These codes were found in them.")
    v_sorted = sorted(vitals, key=lambda x: vitals[x], reverse=True)
    for v in v_sorted:
        print(F"{vitals[v]:6} {v}")


def print_prefixes(dir_path: Path) -> NoReturn:
    extensions = list_prefixes(dir_path)
    print(F"File prefixes found in {dir_path}")
    for ext, count in extensions.items():
        print(F"{count:6} {ext}")


def print_categories(dir_path: Path, only_first, *, one_prefix) -> NoReturn:
    """

    :param dir_path:
    :param only_first:
    :param one_prefix:
    :return:
    """
    c_sorted, counter, count = list_categories(dir_path, only_first, one_prefix=one_prefix)
    print(F"Categories found in {count} files in {dir_path}")

    c2 = 0
    for index, key in enumerate(c_sorted):
        print(F"{index:3}: {key:.<32}: {counter[key]:>6}")
        c2 += counter[key]
    print(F"                                       {"======":>6}")
    print(F"{"":3}  Total categories found..........: {c2:>6}")
    print("Some files have more than one category. In particular, many files have both 'Lab' and 'Laboratory'")

    return counter


def parse_args():
    parser = argparse.ArgumentParser(description='Explore Kaiser Health Data',
                                     epilog='Example usage: python health.py -s Weight, --plot, --print')

    parser.add_argument('-a', '--allergy', action=argparse.BooleanOptionalAction,
                        help='Print all active allergies.')
    parser.add_argument('--after', type=str,
                        help='YYYY-MM-DD format date. Only include dates after this date when using --stat.')
    parser.add_argument('-c', '--conditions', action=argparse.BooleanOptionalAction,
                        help='Print all active conditions.')
    parser.add_argument('--categories', action=argparse.BooleanOptionalAction,
                        help='Print all active categories.')
    parser.add_argument('--csv-format', action=argparse.BooleanOptionalAction,
                        help='Format printed output as csv')
    parser.add_argument('-d', '--document-types', action=argparse.BooleanOptionalAction,
                        help='Show the types of documents in the clinical-records directory')
    parser.add_argument('-g', '--generic', type=str,
                        help='Lets you specify a category and a code, like -g Vital-signs:Weight. See --categories')
    parser.add_argument('-l', '--list-vitals', action=argparse.BooleanOptionalAction,
                        help='List names of all vital signs that were found.')
    parser.add_argument('-m', '--medicines', action=argparse.BooleanOptionalAction,
                        help='List all active medicines that were found.')
    parser.add_argument('--medicines-all', action=argparse.BooleanOptionalAction,
                        help='List all active medicines that were found.')
    parser.add_argument('--plot',  action=argparse.BooleanOptionalAction,
                        help='Plots the vital statistic selected with --stat.')
    parser.add_argument('--procedures', action=argparse.BooleanOptionalAction,
                        help='Prints the procedures found.')
    parser.add_argument('--print', action=argparse.BooleanOptionalAction,
                        help='Prints the vital statistic selected with --stat.')
    parser.add_argument('--source', type=str,
                        help='Sets the source directory for the data.', default="export/apple_health_export")
    parser.add_argument('-s', '--stat', type=str,
        help='Print a vital statistic, like weight. Name has to match EXACTLY, ' +
            'Weight" is not "weight".\nSome examples:\n' +
            'SpO2, Weight, "Blood Pressure" (quotes are required, if the name has spaces in it).' +
            'use the -l to get a list of stats found in your data.')
    args = parser.parse_args()
    active = [args.allergy, args.conditions, args.document_types, args.list_vitals, args.medicines, args.medicines_all,
              args.categories, args.stat, args.generic, args.procedures]
    flags = ["-a", "-c", "-d", "-l", "-m", "--medicines-all", "--categories", "-s", "-g", "--procedures"]
    return args, active, flags


def do_vital(condition_path: Path, vital: str, after: str, print_data: bool, vplot: bool, csv_format: bool,
             *, category_name) -> NoReturn:
    if not print_data and not vplot:
        print("You need to select at least one of --plot or --print with --stat")
        return

    ws = extract_all_values(yield_observation_files(condition_path), stat_info=StatInfo(category_name, vital))

    if after:
        ad = datetime.strptime(after, '%Y-%m-%d')
        ws = [w for w in ws if ad < datetime.strptime(w.date, '%Y-%m-%dT%H:%M:%SZ')]

    if not ws:
        print(F"No numerical data was found for stat {vital} ")
        if after:
            print(F"In the range of values after {after}")
        print(F"You can use the -l argument to see what stats are in your data.")
        return
    if print_data:
        print_values(ws, csv_format)
    # if print_min_max:
    #     min = min(wc,key=lambda wc: )

    if vplot:
        dates = [observation.date for observation in ws]
        # Assume lists are homogenous (all have same number and type of fields)
        first = ws[0]
        # Assume all valueQuantities are either list, or not list.
        if len(first.data) == 2:
            # The only multivalued field I have seen so far is blood pressure, with two values.
            values_1 = [observation.data[0].value for observation in ws]
            values_2 = [observation.data[1].value for observation in ws]
            data_name_1 = first.data[0].name
            data_name_2 = first.data[1].name
        elif len(first.data) == 1:
            values_1 = [observation.data[0].value for observation in ws]
            values_2 = None
            data_name_1 = vital
            data_name_2 = None
        else:
            raise ValueError(f"Unexpected number of data values. {len(first.data)}.")

        plot(dates, values_1, values_2, vital, data_name_1, data_name_2)


def go():
    args, active, flags = parse_args()
    base = Path("export/apple_health_export")
    base = Path(args.source)
    condition_path = base / "clinical-records"

    if not any(active):
        print(F"Please select one of {flags} to get some output.")
        return

    if args.conditions:
        print_conditions(condition_path, args.csv_format, "Condition*.json")

    if args.allergy:
        print_conditions(condition_path, args.csv_format, "All*.json")

    if args.procedures:
        print_procedures(condition_path, args.csv_format, "Procedure*.json")

    if args.medicines or args.medicines_all:
        include_inactive = False
        if args.medicines_all:
            include_inactive = True
        print_medicines(condition_path, args.csv_format, "MedicationRequest*.json", include_inactive)

    if args.stat:
        do_vital(condition_path, args.stat, args.after, args.print, args.plot, args.csv_format, category_name="Vital Signs")

    if args.list_vitals:
        print_vitals(observation_files=yield_observation_files(condition_path), category="Vital Signs")

    if args.generic:
        param = args.generic.split("#", 1)
        assert isinstance(param, list)
        if len(param) == 1:
            print_vitals(observation_files=yield_observation_files(condition_path), category=param[0])
        elif len(param) == 2:
            do_vital(condition_path, param[1], args.after, args.print, args.plot, args.csv_format,
                     category_name=param[0])
        else:
            print("Invalid format: use -g category:code     like '-g \"Vital Signs:Blood Pressure\"")

    if args.categories:
        print_categories(condition_path, only_first=False, one_prefix=None)

    if args.document_types:
        print_prefixes(condition_path)

if __name__ == "__main__":
    go()
