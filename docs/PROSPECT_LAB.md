# Prospect Intelligence Lab

A safe first automation experiment for the Client Acquisition OS repository.

## What it does

- Runs manually, on changes to this experiment branch, and every Monday at 13:17 UTC once the workflow is on the default branch.
- Reads rows from data/prospects.csv.
- Makes a bounded HTTP GET request to each supplied public business website.
- Records the HTTP result and, when available, the page title.
- Gives each row a transparent research-completeness score out of 100.
- Creates a Markdown report and CSV results, then uploads both as a downloadable GitHub Actions artifact.

## What it deliberately does not do

- It does not send email, LinkedIn messages, invitations, or contact forms.
- It does not scrape LinkedIn or bypass website restrictions.
- It does not claim to verify decision-maker identity, ad spend, reviews, hiring, revenue, or buying intent.
- It does not require an AI API key or paid service.
- It does not write generated reports back into the repository; reports are attached to the workflow run for 14 days.

## Add prospects

Edit data/prospects.csv and add one row per business. Keep commas inside a field quoted. Use source URLs that support the facts entered.

| Column | What to enter |
|---|---|
| company | Business name |
| niche | Industry |
| website | Public business website URL |
| decision_maker | Person's name, only when sourced |
| role | Current role, only when sourced |
| linkedin_url | Direct personal profile URL, if verified |
| source_url | Public source supporting the key observation |
| observed_signal | Specific fact observed, not a guess |
| service_fit | Meta Ads, Google Ads, website development, or reputation management; mark as hypothesis if not confirmed |
| notes | Short context or manual follow-up task |

Only the company field is required for a row to be processed. Missing fields lower the completeness score.

## Run it

1. Open the repository on GitHub.
2. Switch to the experiment/prospect-intelligence-lab branch.
3. Add prospects to data/prospects.csv and commit the change.
4. Open Actions and select Prospect Intelligence Lab.
5. Choose Run workflow if that option is available for the branch.
6. Open the completed run and download the prospect-intelligence-lab-report artifact.

The workflow may not appear in the manual-run selector until GitHub recognizes it. After merging the workflow into the default branch, manual and scheduled runs are available there.

## Score meaning

The score measures whether the research record contains expected fields and whether the supplied website responded during this run. It is not a lead-quality score, evidence of commercial intent, or verification badge. A website may fail to respond even when the business is legitimate.

## Local test

Run python scripts/prospect_lab.py. Python 3.10+ is recommended. No third-party packages are required.
