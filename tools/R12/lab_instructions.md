Read the exact task statement, original source and hint-site manifest. Return one
hint for every site in the manifest's order, using only its identifiers and,
for a call site, its approved local proof callees. Every hint is one JSON string:
an expression site's hint is one expression; a call site's hint is one string of
calls separated by semicolons, such as "F(a); G(b)", never a JSON list. An
identifier that the site does not list (a function name included) is rejected.
Do not add declarations, attributes, assumptions, imports, comments, strings,
newlines or control flow. Feedback concerns the named earlier candidate only.
An empty diagnostic list or score 0 is not proof acceptance. The trusted native
full gate determines success.
