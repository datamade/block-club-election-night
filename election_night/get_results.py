import csv
import datetime
import os
import re

from chi_elections import SummaryClient


client = SummaryClient(url="https://chicagoelections.gov/results/ap/SummaryExport.txt")
client.fetch()

output_directory = os.path.join(
    os.getcwd(),
    "results",
    datetime.datetime.now().isoformat(),
)

os.mkdir(output_directory)

police_district_results = []
referendum_results = []

for race in client.races:
    if race.name == "Totals":
        print(race.serialize())
        continue

    race_name = re.sub(r"(Council Member,|Alderperson|Chicago Police Department)\s", "", race.name)

    if race.reporting_unit_name == "POLICE":
        race_name = f"{race_name} Council"

    race_results = []

    for candidate in race.candidates:
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
            race.precincts_total,
        ]

        if race.reporting_unit_name == "POLICE":
            police_district_results.append(row)
        elif race.reporting_unit_name == "SPECIAL REFERENDUM":
            referendum_results.append(row)
        else:
            race_results.append(row)

    if race.reporting_unit_name not in ("POLICE", "SPECIAL REFERENDUM"):
        with open(os.path.join(output_directory, f"{race_name}.csv"), "w") as output_file:
            writer = csv.writer(output_file)
            writer.writerow(["Candidate", "Votes Total", "Votes Percent"])
            writer.writerows(row[1:4] + [""] for row in race_results)
            precincts_reporting = race_results[0][-2]
            precincts_total = race_results[0][-1]
            writer.writerow([
                f"{precincts_reporting} of {precincts_total} precincts reporting", "", "",
            ])


for file, contents, first_column in (
    ("Police Councils.csv", police_district_results, "District"),
    ("Misc.csv", referendum_results, "Question")
):
    with open(os.path.join(output_directory, file), "w") as output_file:
        writer = csv.writer(output_file)
        writer.writerow([
            first_column,
            "Candidate",
            "Votes Total",
            "Votes Percent",
            "Precincts Reporting",
            "Precincts Total"
        ])
        writer.writerows(contents)
