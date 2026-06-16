"# FILE EDITING RULES
1. DO NOT use the `replace_in_file` tool if you need to modify more than 20 lines of code, or if the file has complex indentation.
2. If `replace_in_file` fails once, IMMEDIATELY switch to `write_to_file` and rewrite the whole file. Do not loop or retry failed replacements.
3. When using `replace_in_file`, ensure that the `SEARCH` block exactly matches the existing code, including all spaces, tabs, and newlines.
4. Prefer rewriting the entire file using `write_to_file` for small to medium files (under 200 lines) to avoid search-and-replace mismatches.

# CODE QUALITY & STYLE
1. Always keep existing code formatting, indentation, and code style.
2. Do not delete existing comments or business logic unless explicitly asked.
3. Always verify that your changes do not break existing imports or exports."