
import os
import requests
from bs4 import BeautifulSoup
import csv

# --- Read batch parameters from GitHub Action inputs ---
start = int(os.getenv("START", 0))
end = int(os.getenv("END", 100))
year = int(os.getenv("YEAR", 2024))

prefix = f"CR{year}-"
case_numbers = [f"{prefix}{str(i).zfill(6)}" for i in range(start, end + 1)]

urls = [
    f'https://www.superiorcourt.maricopa.gov/docket/CriminalCourtCases/caseInfo.asp?caseNumber={case}'
    for case in case_numbers
]

results = []

for case_number, url in zip(case_numbers, urls):
    try:
        req = requests.get(url)
        soup = BeautifulSoup(req.content, "html.parser")

        table = soup.find("div", id="tblDocket12")
        first_charge = None

        if table:
            rows = table.find_all("div", class_='row g-0')

            for row in rows:
                divs = row.find_all("div")
                for i in range(len(divs)):
                    if "Description" in divs[i].get_text(strip=True):
                        description = divs[i + 1].get_text(strip=True)

                        if not first_charge:
                            first_charge = description

                        if any(word in description.upper() for word in ["MURDER", "MANSLAUGHTER", "NEGLIGENT HOMICIDE"]):
                            first_charge = description
                            break
                else:
                    continue
                break

        results.append({
            "Case Number": case_number,
            "URL": url,
            "First Charge": first_charge or "No charge found"
        })

    except Exception as e:
        print(f"Error with {url}: {e}")
        results.append({
            "Case Number": case_number,
            "URL": url,
            "First Charge": f"Error: {e}"
        })

# Save to CSV with dynamic filename
csv_filename = f"charges_{prefix}{start}-{end}.csv"
with open(csv_filename, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=["Case Number", "URL", "First Charge"])
    writer.writeheader()
    writer.writerows(results)

print(f"\nSaved to {csv_filename}")
