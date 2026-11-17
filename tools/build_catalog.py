#!/usr/bin/env python3
"""Build the MCP server catalog that is embedded in static/index.html.

Steps (all optional, run in this order):
  fetch   read every name in curated.json from the official MCP registry
          and normalize it to tools/servers.json
  probe   send one `server/discover` request (protocol 2026-07-28) to each
          remote URL and store the result as the V2 flag
  inject  write tools/servers.json into static/index.html

Usage:
  python3 tools/build_catalog.py fetch probe inject

Only the Python standard library is used. Nothing is sent except the registry
lookups and one unauthenticated JSON-RPC request per remote server.
"""
import concurrent.futures
import datetime
import json
import pathlib
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
CURATED = HERE / "curated.json"
MANUAL = HERE / "manual.json"
TITLES = HERE / "titles.json"
OUT = HERE / "servers.json"
PAGE = ROOT / "static" / "index.html"
REGISTRY = "https://registry.modelcontextprotocol.io/v0/servers/{}/versions/latest"
UA = "mcp-catalog-builder/1.0"
V2 = "2026-07-28"
START, END = "/*CATALOG_START*/", "/*CATALOG_END*/"


def http_json(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


# ---------- normalize registry entries ----------

def key(name):
    """Turn any name into a CAPITAL_WORDS_WITH_UNDERSCORE parameter key."""
    k = re.sub(r"[^A-Za-z0-9]+", "_", re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)).strip("_").upper()
    return k or "VALUE"


class Params:
    def __init__(self):
        self.items = {}

    def add(self, k, meta=None, required=None):
        meta = meta or {}
        p = self.items.setdefault(k, {"key": k, "desc": "", "required": False, "secret": False})
        if meta.get("description") and not p["desc"]:
            p["desc"] = " ".join(meta["description"].split())[:300]
        if meta.get("isRequired") or required:
            p["required"] = True
        if meta.get("isSecret"):
            p["secret"] = True
        hint = meta.get("default") or meta.get("placeholder")
        if hint and not meta.get("isSecret") and "hint" not in p:
            p["hint"] = str(hint)
        return "${" + k + "}"


def subst(template, variables, params, description=None):
    """Replace {var} with ${VAR} and register VAR as a parameter."""
    env_style = re.fullmatch(r"([A-Z][A-Z0-9_]*)=\{[A-Za-z0-9_.-]+\}", template)

    def rep(m):
        name = m.group(1)
        meta = dict((variables or {}).get(name) or {})
        if description and not meta.get("description"):
            meta["description"] = description
        # `-e NAME={var}` keeps NAME as the parameter key
        return params.add(env_style.group(1) if env_style else key(name), meta)
    return re.sub(r"\{([A-Za-z0-9_.-]+)\}", rep, template)


def render_args(arguments, params, keep_flags):
    out = []
    for a in arguments or []:
        variables = a.get("variables")
        value = a.get("value")
        if a.get("type") == "named":
            if value is not None:
                out += [a["name"], subst(str(value), variables, params, a.get("description"))]
            elif a.get("isRequired"):
                out += [a["name"], params.add(key(a["name"]), a, required=True)]
            elif keep_flags:
                out.append(a["name"])
            # optional named arguments without a fixed value are left out
        else:
            if value is not None:
                out.append(subst(str(value), variables, params, a.get("description")))
            elif a.get("isRequired"):
                out.append(params.add(key(a.get("valueHint") or a.get("name") or "ARGUMENT"), a, required=True))
    return out


def normalize_package(p):
    if p.get("transport", {}).get("type") != "stdio":
        return None
    rt, ident = p.get("registryType"), p.get("identifier")
    params = Params()
    env = {}
    for e in p.get("environmentVariables") or []:
        if e.get("value") is not None:
            env[e["name"]] = subst(str(e["value"]), e.get("variables"), params)
        else:
            env[e["name"]] = params.add(key(e["name"]), e)
    runtime = render_args(p.get("runtimeArguments"), params, keep_flags=True)
    package = render_args(p.get("packageArguments"), params, keep_flags=False)
    if rt == "npm":
        command, args, label = "npx", runtime + ["-y", ident] + package, "Local (npx)"
    elif rt == "pypi":
        command, args, label = "uvx", runtime + [ident] + package, "Local (uvx)"
    elif rt == "nuget":
        command, args, label = "dnx", runtime + [ident, "--yes"] + package, "Local (dnx)"
    elif rt == "oci":
        command, label = "docker", "Local (docker)"
        image = ident if (":" in ident.split("/")[-1] or not p.get("version")) else ident + ":" + p["version"]
        if "run" in runtime + package:
            args = runtime + package  # the entry spells out the full docker command
            if not any(image.split(":")[0] in a for a in args):
                args.append(image)
        else:
            args = ["run", "-i", "--rm"]
            for name in env:
                args += ["-e", name]
            args += runtime + [image] + package
    else:
        return None
    return {"kind": "stdio", "label": label, "command": command, "args": args, "env": env,
            "params": list(params.items.values())}


def normalize_remote(r):
    params = Params()
    url = subst(r["url"], r.get("variables"), params)
    headers = {}
    for h in r.get("headers") or []:
        if h.get("value") is not None:
            headers[h["name"]] = subst(str(h["value"]), h.get("variables"), params)
        elif h["name"].lower() == "authorization" and "bearer" in (h.get("description") or "").lower():
            headers[h["name"]] = "Bearer " + params.add("API_TOKEN", h)
        else:
            headers[h["name"]] = params.add(key(h["name"]), h)
    kind = "sse" if r["type"] == "sse" else "http"
    return {"kind": kind, "label": "Remote (SSE)" if kind == "sse" else "Remote (HTTP)",
            "url": url, "headers": headers, "params": list(params.items.values())}


def normalize(name, group, server):
    options, seen = [], set()
    remotes = [normalize_remote(r) for r in server.get("remotes") or []]
    http = [r for r in remotes if r["kind"] == "http"] or remotes
    for r in http:
        if r["url"] not in seen and len(options) < 4:
            seen.add(r["url"])
            options.append(r)
    types = set()
    for rt in ("npm", "pypi", "oci", "nuget"):
        for p in server.get("packages") or []:
            if p.get("registryType") == rt and rt not in types and len(types) < 2:
                n = normalize_package(p)
                if n:
                    types.add(rt)
                    options.append(n)
    if len([o for o in options if o["kind"] != "stdio"]) > 1:
        for o in options:
            if o["kind"] != "stdio":
                o["label"] += " " + urllib.parse.urlparse(o["url"].replace("${", "").replace("}", "")).netloc
    titles = json.loads(TITLES.read_text()) if TITLES.exists() else {}
    title = titles.get(name) or server.get("title") or name.split("/")[0].split(".")[-1].capitalize()
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-") or "server"
    return {
        "id": name, "slug": slug, "name": title, "group": group,
        "desc": " ".join((server.get("description") or "").split()),
        "link": server.get("websiteUrl") or (server.get("repository") or {}).get("url") or "",
        "source": "registry", "options": options, "v2": None,
    }


def fetch():
    curated = json.loads(CURATED.read_text())
    manual = json.loads(MANUAL.read_text()) if MANUAL.exists() else []
    servers, failed = [], []

    def one(item):
        group, name = item
        try:
            data = http_json(REGISTRY.format(urllib.parse.quote(name, safe="")))
            return normalize(name, group, data["server"])
        except Exception as e:  # noqa: BLE001
            failed.append((name, str(e)))
            return None

    todo = [(g, n) for g, names in curated.items() for n in names]
    with concurrent.futures.ThreadPoolExecutor(8) as ex:
        servers = [s for s in ex.map(one, todo) if s and s["options"]]
    servers = manual + servers
    used = {}
    for s in servers:  # unique config names
        used[s["slug"]] = used.get(s["slug"], 0) + 1
        if used[s["slug"]] > 1:
            s["slug"] += "-" + re.sub(r"[^a-z0-9]+", "-", s["id"].split("/")[-1].lower()).strip("-")
    order = list(curated.keys())
    save({"generated": now(), "groups": order, "servers": servers})
    print(f"fetch: {len(servers)} servers, {len(failed)} failed")
    for f in failed:
        print("  failed:", *f)


# ---------- V2 probe ----------

def probe_one(url):
    """Return (v2, note). v2 is True, False or None (unknown)."""
    body = json.dumps({
        "jsonrpc": "2.0", "id": 1, "method": "server/discover",
        "params": {"_meta": {
            "io.modelcontextprotocol/protocolVersion": V2,
            "io.modelcontextprotocol/clientInfo": {"name": "mcp-catalog-builder", "version": "1.0"},
            "io.modelcontextprotocol/clientCapabilities": {},
        }},
    }).encode()
    req = urllib.request.Request(url, data=body, method="POST", headers={
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "MCP-Protocol-Version": V2,
        "Mcp-Method": "server/discover",
        "User-Agent": UA,
    })
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            status, text = r.status, r.read(20000).decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        status, text = e.code, e.read(20000).decode("utf-8", "replace")
    except Exception as e:  # noqa: BLE001
        return None, f"no answer ({type(e).__name__})"
    if status in (401, 403):
        return None, f"login required (HTTP {status})"
    msg = None
    for chunk in [text] + [l[5:] for l in text.splitlines() if l.startswith("data:")]:
        try:
            cand = json.loads(chunk)
            if isinstance(cand, dict) and cand.get("jsonrpc") == "2.0":
                msg = cand
                break
        except ValueError:
            continue
    if msg is None:
        return None, f"no JSON-RPC answer (HTTP {status})"
    if "result" in msg and status == 200:
        return True, "answered server/discover"
    err = msg.get("error") or {}
    supported = (err.get("data") or {}).get("supported") if isinstance(err.get("data"), dict) else None
    if supported:
        return (V2 in supported), "supports " + ", ".join(map(str, supported))
    return False, f"rejected server/discover (HTTP {status}, code {err.get('code')})"


def probe():
    data = json.loads(OUT.read_text())
    jobs = []
    for s in data["servers"]:
        for o in s["options"]:
            if o["kind"] != "stdio" and "${" not in o["url"]:
                jobs.append((s, o["url"]))
                break
    with concurrent.futures.ThreadPoolExecutor(12) as ex:
        results = list(ex.map(lambda j: probe_one(j[1]), jobs))
    count = {True: 0, False: 0, None: 0}
    for (s, _), (v2, note) in zip(jobs, results):
        s["v2"], s["v2note"] = v2, note
        count[v2] += 1
    data["probed"] = now()
    save(data)
    print(f"probe: {len(jobs)} remote servers, V2 yes {count[True]}, no {count[False]}, unknown {count[None]}")


# ---------- inject ----------

def inject():
    data = json.loads(OUT.read_text())
    html = PAGE.read_text()
    a, b = html.index(START), html.index(END)
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    PAGE.write_text(html[:a + len(START)] + payload + html[b:])
    print(f"inject: {len(data['servers'])} servers into {PAGE.relative_to(ROOT)}")


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")


def save(data):
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n")


if __name__ == "__main__":
    steps = {"fetch": fetch, "probe": probe, "inject": inject}
    for step in sys.argv[1:] or ["fetch", "probe", "inject"]:
        steps[step]()
