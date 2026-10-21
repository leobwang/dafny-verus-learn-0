Read the exact task statement, original source and hint-site manifest. Return one
hint for every site in the manifest's order. Every hint is one JSON string: an
expression site's hint is one expression; a decreases site's hint is one
termination measure (an expression); a call site's hint is one string of calls
to its approved local proof callees separated by semicolons, such as
"F(a); G(b)", never a JSON list. Any name in scope may appear in a hint; a name
that does not resolve makes the candidate fail verification.
Do not add declarations, attributes, assumptions, imports, comments, strings,
newlines or control flow. Feedback concerns the named earlier candidate only.
An empty diagnostic list or score 0 is not proof acceptance. The trusted native
full gate determines success.
