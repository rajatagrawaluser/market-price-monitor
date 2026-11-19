#market-price-monitor

Logs the US Dollar Index (DXY), gold and silver prices to prices.csv every weekday at 10:00 IST, using GitHub Actions.

Files
price_monitor.py: fetches prices from Yahoo Finance and prints or appends them to CSV.
.github/workflows/prices.yml: runs the script on a schedule and commits prices.csv back to the repo.
Run manually
Open the Actions tab.
Select Daily price log.
Click Run workflow.
Run locally
bash
pip install yfinance
python price_monitor.py --once --csv prices.csv
