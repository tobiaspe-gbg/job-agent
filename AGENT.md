# The Job Finder Agent

## Business Requirements

This project is building a Job Finder Agent
- the agent searches for relevant job openings among official Swedish job sites
- found open positions are matched against named keywords, stated roles of interest and any uploaded CV
- CVs are found in the CV folder, roles of interest are as stated
- jobs found are the matched against the criteria and given a score of relevance
- all found job entries shall be kept in a DB, with a 30 day automatic retention
- no job / position shall be sent twice, so keeping track for what was found earlier is needed
- a daily send-out per mail will list all new open roles of relevance
- the mail send-out shall be formatted nicely, to make it minimal and highly readable
- mail recipient is specified in the `.email` file; SMTP settings live in `.env`

### Roles of interest
- automotive assembly operator
- breakfast or bar hostess
- event staff
- house-keeping staff
- front-desk at hotels or bars
- waiting staff at restaurants

### Location filter
- Only jobs within 30 km of Prebendegatan 6, Göteborg

## Limitations


## Technical Decisions

- - Use OpenRouter for the AI calls. An OPENROUTER_API_KEY is in .env in the project root
- Use `openai/gpt-oss-120b` as the model
- Everything packaged into a Docker container
- Use "uv" as the package manager for python in the Docker container
- Use SQLite local database for the database, creating a new db if it doesn't exist
- Start and Stop server scripts for Mac, PC, Linux in scripts/

## Strategy
1. Carry out extensive testing with Playwright or similar


## Coding standards

1. Use latest versions of libraries and idiomatic approaches as of today
2. Keep it simple - NEVER over-engineer, ALWAYS simplify, NO unnecessary defensive programming. No extra features - focus on simplicity.
3. Be concise. Keep README minimal. IMPORTANT: no emojis ever
4. When hitting issues, always identify root cause before trying a fix. Do not guess. Prove with evidence, then fix the root cause.

## Working documentation

All documents for planning and executing this project will be in the docs/ directory.
Please review the docs/PLAN.md document before proceeding.
