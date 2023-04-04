# 🍕 Block Club Election Night

This repository contains code to retrieve results for the February 2023 Municipal Election.

Already performed the setup? [⏩ Jump to instructions for **Running the scraper**.](#running-the-scraper)

## System requirements

- **Python 3.** Download and install the latest version of Python here: https://www.python.org/downloads/
- **Git.** Download and install Git here: https://sourceforge.net/projects/git-osx-installer/

## Setup

Open a command line. On a Mac, you can use the `Terminal` app.

To run a command, type or copy and paste the listed incantation into your command line, then press Enter (or Return).

In the `Terminal` app, navigate to your desktop:

```bash
cd ~/Desktop
```

Download the scraper code:

```bash
git clone https://github.com/datamade/block-club-election-night.git
```

Navigate into the directory containing the scraper code:

```bash
cd block-club-election-night
```

Create and activate a virtual environment, then install the scraper:

```bash
python3 -m venv ~/.virtualenvs/elections
source ~/.virtualenvs/elections/bin/activate
pip install -r requirements.txt
```

## Running the scraper

Whether you want to scrape the summary file or precinct results, you first need to navigate into the directory containing the scraper code and activate your virtual environment. If you just finished setup, above, you can skip this step!

```bash
cd ~/Desktop/block-club-election-night
source ~/.virtualenvs/elections/bin/activate
```

### Scraping the summary file

Run the summary file scraper like this:

```bash
python3 -m election_night.get_results
```

You should see something like this in your terminal:

```
Getting summary results from https://chicagoelections.gov/results/ap/SummaryExport.txt! 🎉
```

This indicates the scrape ran successfully!

You can view the output in the `results/` folder. Output files are grouped in a sub-folder named for the date and time you ran the scrape.

### Scraping precinct-level results

Late on Election Night and into the following day, the Board of Elections stops updating the
summary file in favor of precinct-level results. You can run the precinct scraper like this:

```bash
python -m election_night.get_results --precinct
```

You should see something like this in your terminal:

```
Getting precinct results for 2023 Municipal Runoffs - 4/4/23! 🎉
```

Note that scraping precinct results takes about a minute to run, since the pages are slow to load.

As before, when the scrape completes, you can view the output in the `results/` folder. Output files are grouped in a sub-folder named for the date and time you ran the scrape.