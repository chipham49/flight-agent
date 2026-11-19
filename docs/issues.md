# Issue List: Cheapest Flight Finder (1-week capstone)

How to use this list:
- Make one GitHub issue per item below. Copy the **title** and paste the rest into the description.
- Add the **labels** and **milestone** shown for each one.
- Put every issue on your Project board. Move each card To do → In progress → Done.

## Labels to create first

| Label | Colour idea | Meaning |
|---|---|---|
| `setup` | grey | Getting tools and accounts ready |
| `build` | blue | Code written by Claude Code |
| `eval` | purple | Testing how good the agent is |
| `docs` | green | Writing and documentation |
| `bug` | red | Something the agent got wrong |
| `pm` | orange | Product decisions and planning |
| `backlog` | white | Good idea, but not for this week |

## Milestones to create
`Day 1 – Setup`, `Day 2 – Build agent`, `Day 3 – Build evals`, `Day 4 – Eval round 1`,
`Day 5 – Improve`, `Day 6 – Ship`, `Day 7 – Demo`

---

## Day 1: Setup

### #1 Create the GitHub repo ✅ (already done, so close it right away)
Labels: `setup` · Milestone: Day 1
- [x] Repo `flight-agent` created with a README

**Done when:** the repo exists on GitHub.

### #2 Connect Claude Code to the repo with write access
Labels: `setup` · Milestone: Day 1

**Why:** Claude Code can read the repo but can't save (push) changes yet.
- [ ] Install the Claude GitHub App on my account: https://github.com/apps/claude/installations/select_target
- [ ] Give it access to `flight-agent`
- [ ] Ask Claude Code to make a test change on a branch and push it

**Done when:** Claude Code can push a branch to the repo.

### #3 Create labels and milestones
Labels: `setup` · Milestone: Day 1
- [ ] Create the 7 labels listed at the top of this file
- [ ] Create the 7 milestones (Day 1 to Day 7)

**Done when:** all labels and milestones show up in the Issues tab.

### #4 Set up the Project board
Labels: `setup`, `pm` · Milestone: Day 1
- [ ] Projects tab → New project → Board template
- [ ] Columns: To do / In progress / Done
- [ ] Add every issue to the board

**Done when:** the board shows all issues in "To do".

### #5 Create the Anthropic API key with a spending limit
Labels: `setup` · Milestone: Day 1

**Why:** the agent needs this "prepaid card" to call Claude and search the web.
- [ ] Sign in at console.anthropic.com
- [ ] Add about $10 of credit
- [ ] Set a $10 monthly spending limit
- [ ] Create an API key
- [ ] Save it **only** as a secret in the Claude Code environment settings, never in a file or chat

**Done when:** the key is stored as a secret and the limit is set.

### #6 Update the README title and goal
Labels: `docs` · Milestone: Day 1

**Why:** the README says "Flight Booking Agent", but the agent only searches. It never books.
- [ ] Rename the title to "Cheapest Flight Finder"
- [ ] Add one line: "Finds the 3 cheapest flights for a trip, with source links."

**Done when:** the README matches the real scope.

### #7 Write the problem statement
Labels: `docs`, `pm` · Milestone: Day 1
- [ ] Create `docs/problem-statement.md`
- [ ] Cover: who has the problem, what the problem is, why it matters, what success looks like
- [ ] Add the in-scope and out-of-scope table

**Done when:** the file is committed and fits on one page.

---

## Day 2: Build the agent

### #8 Add CLAUDE.md (project rules for Claude Code)
Labels: `build`, `docs` · Milestone: Day 2
- [ ] Describe the project, the folder layout and the coding style (short, beginner-friendly, commented)
- [ ] Rule: never hardcode the API key
- [ ] Rule: every change goes on a branch with a pull request

**Done when:** `CLAUDE.md` is in the repo root.

### #9 Add .gitignore and requirements.txt
Labels: `build`, `setup` · Milestone: Day 2
- [ ] `.gitignore` blocks `.env`, secrets and Python junk files
- [ ] `requirements.txt` lists the Python packages needed

**Done when:** both files are merged.

### #10 Write the agent's rules (agent/rules.md)
Labels: `build`, `pm` · Milestone: Day 2
- [ ] Ask for missing details (origin, destination, dates)
- [ ] Search at least 2 sources
- [ ] Only show flights that match the exact route and dates
- [ ] Never make up a price, and give every flight a source link
- [ ] Compare total price in USD
- [ ] Flag basic economy, short layovers and overnight layovers
- [ ] Never book or ask for payment
- [ ] Use a fixed output table and add the "prices change fast" disclaimer

**Done when:** `agent/rules.md` is merged.

### #11 Build the flight finder (agent/find_flights.py)
Labels: `build` · Milestone: Day 2
- [ ] Takes a trip as text, e.g. `python agent/find_flights.py "LAX to NYC, Dec 10"`
- [ ] Uses the Claude API with the web search tool and follows `rules.md`
- [ ] Prints the top 3 flights as a table
- [ ] Reads the API key from an environment variable
- [ ] Shows a friendly message if something goes wrong

**Done when:** it runs and prints a table for a real trip.

### #12 Test the agent with 3 sample trips
Labels: `eval` · Milestone: Day 2
- [ ] One domestic, one international, one with a missing date
- [ ] Paste the outputs into the pull request description

**Done when:** all 3 runs are recorded in the PR.

### #13 Review and merge the `build-agent` pull request
Labels: `pm` · Milestone: Day 2
- [ ] Ask Claude Code to "explain this PR in plain English"
- [ ] Read every changed file name and its purpose
- [ ] Merge, then delete the branch

**Done when:** the PR is merged into `main`.

---

## Day 3: Build the evals

### #14 Create the 10 test trips (evals/test-trips.csv)
Labels: `eval` · Milestone: Day 3
- [ ] 5 domestic trips
- [ ] 2 international trips
- [ ] 2 vague trips (e.g. "cheap flight to london next month")
- [ ] 1 impossible trip (a date in the past)
- [ ] Columns: id, trip_text, type, expected_behaviour

**Done when:** the CSV has 10 rows and shows as a table on GitHub.

### #15 Build the eval runner (evals/run_evals.py)
Labels: `build`, `eval` · Milestone: Day 3
- [ ] Runs the agent on every test trip
- [ ] Saves `evals/results/round-N.csv`
- [ ] Automatic columns: top_price, airline, has_source_link, followed_format, cost_usd, seconds
- [ ] Empty columns for me to fill in: cheapest_on_google_flights, within_10_percent, notes

**Done when:** one command produces a results CSV.

### #16 Review and merge the `add-evals` pull request
Labels: `pm` · Milestone: Day 3
- [ ] Ask Claude Code for a plain-English summary
- [ ] Merge and delete the branch

**Done when:** the PR is merged.

---

## Day 4: Eval round 1

### #17 Run eval round 1 and commit the results
Labels: `eval` · Milestone: Day 4
- [ ] Ask Claude Code: "Run the evals as round 1 and commit the results"
- [ ] Check that the cost stayed under $3

**Done when:** `evals/results/round-1.csv` is in the repo.

### #18 Check round 1 prices by hand on Google Flights
Labels: `eval`, `pm` · Milestone: Day 4
- [ ] For each trip, find the cheapest price on Google Flights
- [ ] Fill in `cheapest_on_google_flights` and `within_10_percent` (Y/N)
- [ ] Write the round 1 score: __/10

**Done when:** every row is filled in and the score is written down.

### #19 Log each failure as a bug issue
Labels: `bug` · Milestone: Day 4

Make one new issue per problem, using this template:
```
Title: Bug: <what went wrong>
Trip: <which test trip>
Expected: <what should happen>
Actual: <what happened>
How bad: High / Medium / Low
```
**Done when:** every failure from round 1 has its own bug issue.

### #20 Prioritise the top 3 fixes
Labels: `pm` · Milestone: Day 4
- [ ] Rank the bug issues by how bad each is and how often it happens
- [ ] Choose the top 3 to fix tomorrow, and move the rest to `backlog`
- [ ] Write down why in a comment on this issue

**Done when:** 3 bugs are chosen and the reason is written.

---

## Day 5: Improve

### #21 Fix the top 3 bugs on the `improve-rules` branch
Labels: `build` · Milestone: Day 5
- [ ] Ask Claude Code to fix the chosen bugs (change the rules first, and the code only if needed)
- [ ] Link the bug issues in the PR with `Closes #__`

**Done when:** the PR is open with the fixes.

### #22 Run eval round 2 and compare with round 1
Labels: `eval` · Milestone: Day 5
- [ ] Run the evals as round 2
- [ ] Check prices by hand again
- [ ] Add a before/after table to the PR description

**Done when:** `round-2.csv` exists and the comparison is in the PR.

### #23 Review and merge the `improve-rules` pull request
Labels: `pm` · Milestone: Day 5
- [ ] Read the plain-English summary
- [ ] Confirm the score improved, or explain why it didn't
- [ ] Merge, and check the linked bugs closed automatically

**Done when:** the PR is merged. Screenshot it for the slides.

---

## Day 6: Ship

### #24 Finish the README
Labels: `docs` · Milestone: Day 6
- [ ] Problem, how it works (with the diagram) and how to run it
- [ ] Round 1 vs round 2 results table
- [ ] Links to the problem statement and learnings

**Done when:** a stranger could understand and run the project from the README.

### #25 Write the learnings (docs/learnings.md)
Labels: `docs`, `pm` · Milestone: Day 6
- [ ] What worked
- [ ] What didn't, and why (e.g. some flight sites hide prices from search)
- [ ] What I'd build next

**Done when:** the file is committed.

### #26 Publish Release v1.0
Labels: `pm` · Milestone: Day 6
- [ ] Releases → Draft a new release → tag `v1.0`
- [ ] Write short release notes: what it does and its scores

**Done when:** v1.0 shows on the repo's home page.

### #27 Build the presentation slides
Labels: `pm` · Milestone: Day 6

Slides:
- [ ] Problem
- [ ] Solution and diagram
- [ ] Live demo
- [ ] Eval results (round 1 vs round 2)
- [ ] "How I managed it" (board, PR and release screenshots)
- [ ] Learnings and next steps

**Done when:** the slides are complete.

---

## Day 7: Demo

### #28 Rehearse the demo
Labels: `pm` · Milestone: Day 7
- [ ] Practise twice and time it (under 3 minutes)
- [ ] Record a backup video in case live search fails on the day

**Done when:** the demo has been rehearsed and the backup video saved.

### #29 Final cleanup
Labels: `pm` · Milestone: Day 7
- [ ] Every card on the board is in Done (or in Backlog)
- [ ] No API key appears anywhere in the repo
- [ ] All branches are merged or deleted

**Done when:** the repo and board are tidy.

---

## Backlog (good ideas, not for this week)

| # | Title | Label |
|---|---|---|
| #30 | Flexible dates (±3 days) | `backlog` |
| #31 | Price drop alerts | `backlog` |
| #32 | Use a real flight-data API instead of web search | `backlog` |
| #33 | Simple web page instead of the command line | `backlog` |
| #34 | Include baggage fees in the total price | `backlog` |
| #35 | Multi-city and group trips | `backlog` |
