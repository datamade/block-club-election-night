import csv
import datetime
import os
import re

from chi_elections import SummaryClient


client = SummaryClient(url="https://chicagoelections.gov/results/ap/SummaryExport.txt")
client.fetch()

municipal = []
ward = []
police_district = []
referendum = []

for race in client.races:
    if race.name == "Totals":
        print(race.serialize())
        continue

    for candidate in race.candidates:
        race_name = re.sub(r"(Council Member,|Alderperson|Chicago Police Department)\s", "", race.name)

        if race.reporting_unit_name == "POLICE":
            race_name = f"{race_name} Council"

        if race.reporting_unit_name != "SPECIAL REFERENDUM":
            choice_name = candidate.full_name.encode("latin1").decode("utf-8").title()

            if choice_name == "Cb Johnson":
                choice_name = "CB Johnson"
        else:
            choice_name = candidate.full_name

        row = [
            race_name,
            choice_name,
            candidate.vote_total,
            candidate.vote_total / (race.total_ballots_cast or 1) * 100,
            race.precincts_reporting,
            race.precincts_reporting / race.precincts_total * 100,
        ]

        if race.reporting_unit_name == "MUNICIPAL":
            municipal.append(row)
        elif race.reporting_unit_name == "WARD":
            ward.append(row)
        elif race.reporting_unit_name == "POLICE":
            police_district.append(row)
        elif race.reporting_unit_name == "SPECIAL REFERENDUM":
            referendum.append(row)
        else:
            raise ValueError(f"Don't know where to put {row}")

output_directory = os.path.join(
    os.getcwd(),
    "results",
    datetime.datetime.now().isoformat(),
)

os.mkdir(output_directory)

HEADER = (
    "Candidate",
    "Votes",
    "Total Votes Percentage",
    "Precincts Reported",
    "Precincts Percentage",
)

for file, contents, first_column in (
    ("municipal.csv", municipal, "Race"),
    ("alders.csv", ward, "Ward"),
    ("police_district_council.csv", police_district, "District"),
    ("misc.csv", referendum, "Question")
):
    with open(os.path.join(output_directory, file), "w") as output_file:
        writer = csv.writer(output_file)
        writer.writerow([first_column, *HEADER])
        writer.writerows(contents)
