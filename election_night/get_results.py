import csv
import datetime
import os
import re

from chi_elections import SummaryClient
from chi_elections.precincts import elections as PrecinctClient

if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Scrape election results"
    )
    parser.add_argument(
        "--test",
        help="Pass this flag to scrape results from the test URL",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--precinct",
        help="Pass this flag to scrape and aggregate precinct results",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--election",
        help="If passing precinct, specify which election to scrape results from. Default: 2023 Municipal Runoffs - 4/4/23",
        default="2023 Municipal Runoffs - 4/4/23"
    )

    options = parser.parse_args()

    output_directory = os.path.join(
        os.getcwd(),
        "results",
        datetime.datetime.now().isoformat(),
    )

    os.mkdir(output_directory)

    last_updated = f"Last updated at {datetime.datetime.now().strftime('%-I:%M %p on %b %-d, %Y')}"

    if options.precinct:
        print(f"Getting precinct results for {options.election}! 🎉")

        election = PrecinctClient()[options.election]

        for race_name, race_obj in election.races.items():
            race_results = []

            race_name = race_name.replace("Alderperson ", "").strip()

            for k, v in race_obj.total.items():
                if k == "Votes":
                    continue

                row = {
                    "Race Name": race_name,
                    "Candidate": k if k == "CB" else k.title(),
                    "Votes Total": v,
                    "Votes Percent": round(v / (race_obj.total["Votes"] or 1) * 100, 2),
                    "Precincts Reporting": sum(1 for p, p_data in race_obj.precincts.items() if p_data["Votes"] > 0),
                    "Precincts Total": len(race_obj.precincts),
                }

                race_results.append(row)

            with open(os.path.join(output_directory, f"{race_name}.csv"), "w") as output_file:
                writer = csv.DictWriter(
                    output_file,
                    fieldnames=["Candidate", "Votes Total", "Votes Percent"],
                    extrasaction="ignore"
                )

                sorted_results = reversed(
                    sorted(race_results, key=lambda x: x["Votes Percent"])
                )

                writer.writeheader()
                writer.writerows(sorted_results)

                precincts_reporting = race_results[0]["Precincts Reporting"]
                precincts_total = race_results[0]["Precincts Total"]

                final_row = {
                    "Candidate": f"{precincts_reporting} of {precincts_total} precincts reporting",
                    "Votes Total": "",
                    "Votes Percent": last_updated,
                }

                writer.writerow(final_row)

    else:
        if options.test:
            summary_url = "https://chicagoelections.gov/results/ap/SummaryExport.txt"
        else:
            summary_url = "https://chicagoelections.gov/ap/SummaryExport.txt"

        client = SummaryClient(url=summary_url)
        client.fetch()

        if len(client.races) == 1:
            print(f"No results at {summary_url} yet. Please try again after 7 p.m. on Election Night. 🗳")
            sys.exit()

        else:
            print(f"Getting summary results from {summary_url}! 🎉")

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
                    choice_name = candidate.full_name.title()

                    if choice_name == "Cb Johnson":
                        choice_name = "CB Johnson"
                else:
                    choice_name = candidate.full_name

                row = {
                    "Race Name": race_name,
                    "Candidate": choice_name,
                    "Votes Total": candidate.vote_total,
                    "Votes Percent": round(candidate.vote_total / (race.total_ballots_cast or 1) * 100, 2),
                    "Precincts Reporting": race.precincts_reporting,
                    "Precincts Total": race.precincts_total,
                }

                if race.reporting_unit_name == "POLICE":
                    police_district_results.append(row)
                elif race.reporting_unit_name == "SPECIAL REFERENDUM":
                    referendum_results.append(row)
                else:
                    race_results.append(row)

            if race.reporting_unit_name not in ("POLICE", "SPECIAL REFERENDUM"):
                with open(os.path.join(output_directory, f"{race_name}.csv"), "w") as output_file:
                    writer = csv.DictWriter(
                        output_file,
                        fieldnames=["Candidate", "Votes Total", "Votes Percent"],
                        extrasaction="ignore"
                    )

                    sorted_results = reversed(
                        sorted(race_results, key=lambda x: x["Votes Percent"])
                    )

                    writer.writeheader()
                    writer.writerows(sorted_results)

                    precincts_reporting = race_results[0]["Precincts Reporting"]
                    precincts_total = race_results[0]["Precincts Total"]

                    final_row = {
                        "Candidate": f"{precincts_reporting} of {precincts_total} precincts reporting",
                        "Votes Total": "",
                        "Votes Percent": last_updated,
                    }

                    writer.writerow(final_row)


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
                writer.writerows(row.values() for row in contents)
                writer.writerow(["", "", "", "", "", last_updated])
