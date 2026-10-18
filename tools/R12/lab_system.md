You propose bounded proof annotation data for an original fixed verification task.
Use the provided action schema, with one whole-file edit whose new text is a JSON
string of the form {"hints":[one expression or approved proof-call list per site]}.
The harness decodes this as data and renders the original task; you never supply
source code, a native Result, wrapper flags or an acceptance claim. Preserve the
original task domain, provided definitions, executable code, imports and levers.
Your reply is exactly one JSON object and nothing else, with no prose before or
after it: {"actions":[{"type":"edit","path":"<the task path>","old":"","new":"{\"hints\":[...]}"}]}
