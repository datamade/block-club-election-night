import csv
import datetime
import os
import re

from chi_elections import SummaryClient
from chi_elections.precincts import elections as PrecinctClient


class Reporter(object):

    def __init__(self, client):
        self.client = client

        now = datetime.datetime.now()

        self.last_updated_str = (
            f"Last updated at {now.strftime('%-I:%M %p on %b %-d, %Y')}"
        )

        self.output_directory = os.path.join(
            os.getcwd(),
            "results",
            now.isoformat(),
        )

        os.mkdir(self.output_directory)

    def get_results(self):
        raise NotImplementedError

    def parse_result(self):
        raise NotImplementedError

    def write_report(self, race_name, results):
        with open(os.path.join(self.output_directory, f"{race_name}.csv"), "w") as output_file:
            writer = csv.DictWriter(
                output_file,
                fieldnames=["Candidate", "Votes Total", "Votes Percent"],
                extrasaction="ignore"
            )

            sorted_results = reversed(
                sorted(results, key=lambda x: x["Votes Percent"])
            )

            writer.writeheader()
            writer.writerows(sorted_results)

            precincts_reporting = results[0]["Precincts Reporting"]
            precincts_total = results[0]["Precincts Total"]

            final_row = {
                "Candidate": f"{precincts_reporting} of {precincts_total} precincts reporting",
                "Votes Total": "",
                "Votes Percent": self.last_updated_str,
            }

            writer.writerow(final_row)

    def run(self):
        for race_name, race_obj, candidates in self.get_results():
            results = [
                self.parse_result(race_name, race_obj, candidate) for candidate in candidates
            ]

            self.write_report(race_name, results)


class PrecinctReporter(Reporter):

    def get_results(self):
        for race_name, race_obj in self.client.races.items():
            race_name = race_name.replace("Alderperson ", "").strip()
            candidates = {k: v for k, v in race_obj.total.items() if k != 'Votes'}

            yield race_name, race_obj, candidates.items()

    def parse_result(self, race_name, race_obj, candidate):
        choice_name, choice_votes = candidate

        if choice_name.startswith("CB"):
            choice_name = "CB Johnson"
        else:
            choice_name = choice_name.title()

        return {
            "Race Name": race_name,
            "Candidate": choice_name,
            "Votes Total": choice_votes,
            "Votes Percent": round(choice_votes / (race_obj.total["Votes"] or 1) * 100, 2),
            "Precincts Reporting": sum(1 for p, p_data in race_obj.precincts.items() if p_data["Votes"] > 0),
            "Precincts Total": len(race_obj.precincts),
        }


class SummaryReporter(Reporter):

    def get_results(self):
        for race_obj in self.client.races:
            if race_obj.name == "Totals":
                print(race_obj.serialize())
                continue

            race_name = re.sub(r"(Council Member,|Alderperson|Chicago Police Department)\s", "", race_obj.name)

            if race_obj.reporting_unit_name == "POLICE":
                race_name = f"{race_name} Council"

            yield race_name, race_obj, race_obj.candidates

    def parse_result(self, race_name, race_obj, candidate):
        if race_obj.reporting_unit_name != "SPECIAL REFERENDUM":
            choice_name = candidate.full_name.title()

            if choice_name == "Cb Johnson":
                choice_name = "CB Johnson"
        else:
            choice_name = candidate.full_name

        return {
            "Race Name": race_name,
            "Candidate": choice_name,
            "Votes Total": candidate.vote_total,
            "Votes Percent": round(candidate.vote_total / (race_obj.total_ballots_cast or 1) * 100, 2),
            "Precincts Reporting": race_obj.precincts_reporting,
            "Precincts Total": race_obj.precincts_total,
        }


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

    if options.precinct:
        print(f"Getting precinct results for {options.election}! 🎉")

        reporter = PrecinctReporter(
            PrecinctClient()[options.election]
        )

        reporter.run()

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

        reporter = SummaryReporter(client)

        reporter.run()
