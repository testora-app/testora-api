<!-- Load up context prompt: -->

take a look at the app and architecture. Understand deeply how it works inside and out. Ask me any questions if there are things you don't understand. This will be the basis for the rest of our conversation.

<!-- Tool use summaries: -->

After completing a task that involves tool use, provide a quick summary of the work you've done

<!-- Adjust eagerness down: -->

Do not jump into implementation or change files unless clearly instructed to make changed. When the user's intent is ambiguous, default to providing information, doing research, and providing recommendations rather than taking action. Only proceed with edits, modifications, or implementations when the user explicitly requests them.

<!-- Adjust eagerness up: -->
<!-- By default, implement changes rather than only suggesting them. If the user's intent is unclear, infer the most useful likely action and proceed, using tools to discover any missing details instead of guessing. Try to infer the user's intent about whether a tool call (e.g. file edit or read) is intended or not, and act accordingly. -->

<!-- Use parallel tool calls: -->

If you intend to call multiple tools and there are no dependencies
between the tool calls, make all of the independent tool calls in
parallel. Prioritize calling tools simultaneously whenever the
actions can be done in parallel rather than sequentially. For
example, when reading 3 files, run 3 tool calls in parallel to read
all 3 files into context at the same time. Maximize use of parallel
tool calls where possible to increase speed and efficiency.
However, if some tool calls depend on previous calls to inform
dependent values like the parameters, do not call these tools in
parallel and instead call them sequentially. Never use placeholders
or guess missing parameters in tool calls.

<!-- Reduce hallucinations: -->

Never speculate about code you have not opened. If the user
references a specific file, you MUST read the file before
answering. Make sure to investigate and read relevant files BEFORE
answering questions about the codebase. Never make any claims about
code before investigating unless you are certain of the correct
answer - give grounded and hallucination-free answers.

<!--reduce unneeded comments -->

Do not add comments unless they communicate information that cannot be obviously inferred from the code.

<!-- DESIGN -->

Use the frontend design skill when making changes to the UI

<!-- GIT -->

When writing git commits, do not include the claude co-author.

<!-- Component size -->

Try to keep the size of UI components and/or namespaces reasonably small. Some guidelines to use:

1. Functionality. Move unique/composable functionality into its own component/function or namespace.
2. As soon as the number of lines in the code is more than 500, excluding imports, consider a refactor to split out certain functions into their own components/namespaces. This is not a hard rule, and you will have to use good judgement to decide if its necessary to split.

<!--Code reviews -->

before completing any task, run these checks:

- scan for hardcoded secrets, APl keys, passwords
- scan for obviously inefficient/slow code, n + 1 db query patterns, code smells, anti-patterns, etc
- find every security vulnerability in the changes made. think like a pentester. Scan for security issues including but not limited to SQL injection, shell injection, path traversal, XSS attacks, auth bypasses, privilege escalation, input validation gaps, API keys in comments, passwords in config files, tokens in error messages. etc
- verify all user inputs are validated
- run the test suite
- check for type errors

<!-- code reviews 2 -->

After completing all the tasks above, now I want you to carefully read over all of the new code you just wrote and other existing code you just modified with "fresh eyes" looking super carefully for any obvious bugs, errors, problems, issues, confusion, etc. Carefully fix anything you uncover.
