# AI Report

## AI tools used

- I mainly used ChatGPT to validate my thought process for the initial architecture of the application and to critique my implementation. Coming from a JavaScript background, I also took advantage of ChatGPT to mirror concepts in Python to JavaScript (e.g mapping Pydantic/FastAPI concepts to familiar TypeScript and Express patterns) to assist in my understanding. Lastly, I used ChatGPT to help me come up with appropriate tests, and to draft a proper README.md file that covers the entire application. I treated it as a discussion, so that I could also learn while testing my knowledge.

## Example prompts

- "Review this assignment as a senior software engineer coach. Explain what is being assessed and what are some gotchas that I should be looking out for."
- "Compare the FastAPI implementation with an equivalent Express implementation so I can understand the Python concepts through JavaScript."
- "What validation edge cases should I test for schema-driven ingestion?"

## One suggestion I accepted

- I accepted the suggestion to make the dashboard-to-schema relationship explicit with a `schema` property in dashboard configuration. Using an explicit reference avoids naming conventions (such as trade-schema and trade-dashboard) and makes validation straightforward.

## One suggestion I rejected

- I rejected dynamically creating a Pydantic model for every registered schema. For this assignment, a small explicit runtime validator is easier to implement, avoids complexity and enables cleaner error messages for debugging

## How I validated the solution

- Added automated API tests for the happy path, missing required fields, unknown fields, type mismatches, invalid dashboard aggregations, duplicate schemas, and atomic batch ingestion.
- Ran the test suite locally and manually exercised the API through FastAPI's generated `/docs` interface.
