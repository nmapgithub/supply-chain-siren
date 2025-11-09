# Supply Chain Siren 🔔

**Supply Chain Siren** is a focused dependency risk spotlight for Python and JavaScript projects.  
Point it at a repository and it will inspect your manifests, pull live metadata from the package registries, and highlight issues that deserve a closer security review before you merge that pull request.

> **GitHub description**: Spotlight risky dependencies in Python and JavaScript projects with live registry intelligence and clear security signals.

<p align="center">
  <img src="https://img.shields.io/badge/code%20style-black-000000.svg" alt="Code style Black"/>
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License MIT"/>
  <img src="https://img.shields.io/badge/status-alpha-blue.svg" alt="Project status Alpha"/>
</p>

---

## ✨ Highlights

- **Typosquat detection** – fuzzy matches against the most-downloaded ecosystem packages.
- **Release hygiene checks** – flags newly published packages and projects that have not shipped in a long time.
- **Maintainer signal** – warns on single-maintainer projects that are more vulnerable to account takeovers.
- **Adoption telemetry** – low download volume is surfaced as a potential trust risk.
- **Local cache** – registry responses are cached so repeated scans stay fast and minimize upstream noise.

---

## 🚀 Quickstart

> Replace `<GITHUB-USER>` with your GitHub handle once you publish the repository.

```bash
git clone https://github.com/<GITHUB-USER>/supply-chain-siren.git
cd supply-chain-siren

# Build the container once
docker build -t supply-chain-siren .

# Scan the current directory (mounted as /workspace inside the container)
docker run --rm -v ${PWD}:/workspace supply-chain-siren

# Export a JSON report alongside the human readable table
docker run --rm -v ${PWD}:/workspace supply-chain-siren --output /workspace/reports/siren-report.json
```

PowerShell users can substitute `${PWD}` with `$(Get-Location)`; `cmd.exe` users can swap for `%cd%`.

---

## 🛠️ Local Installation (Optional)

```bash
python -m venv .venv
.venv\Scripts\activate            # or: source .venv/bin/activate
pip install -e .

# Run the CLI locally
siren /path/to/repository
```

---

## 📌 Example Output

```
┏━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Package              ┃ Version ┃ Score ┃ Signals                                              ┃
┡━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ reqeusts (pypi)      │ 1.0.0   │ 40    │ Package metadata unavailable; registry lookup failed.│
│ pandas (pypi)        │ 1.5.0   │ 20    │ Single maintainer detected; project is susceptible…  │
└──────────────────────┴─────────┴───────┴──────────────────────────────────────────────────────┘
```

Every row contains:

- **Score** – cumulative heuristic score capped at 100.
- **Signals** – human readable explanations you can paste into issues or PR reviews.

---

## 🔍 What It Checks

| Category          | Signal                                                                 |
|-------------------|-------------------------------------------------------------------------|
| `typosquat`       | Package name is 1–2 edits away from a top ecosystem library             |
| `fresh-release`   | First release is less than 45 days old                                  |
| `stale-package`   | Latest publication is older than one year                               |
| `maintainers`     | Zero or a single maintainer listed in registry metadata                |
| `popularity`      | Weekly download volume below 500                                       |
| `metadata-gaps`   | Registry lookup failed, leaving package metadata unavailable            |

Signals accumulate; higher scores deserve more scrutiny.

---

## 📦 JSON Reporting

Supply Chain Siren can write machine-readable output that you can feed into CI, dashboards, or alerting tools.

```bash
siren /path/to/repository --output reports/siren-report.json
```

Each entry captures the dependency spec, normalized metadata, individual signals, and the aggregate risk score.

---

## 🧪 Tests

```bash
docker build -t supply-chain-siren .
docker run --rm --entrypoint pytest supply-chain-siren tests
```

You can also run `pytest` locally after `pip install -e .[test]`.

---

## 🧭 Roadmap

- Poetry lockfile (TOML) parsing
- GitHub advisory & CVE enrichment
- Malware feed heuristics
- GitHub Action for automated pull-request comments

Ideas or contributions are welcome—open an issue to discuss bigger proposals.

---

## 🤝 Contributing

1. Fork and create a topic branch.
2. Install dependencies with `pip install -e .[test]`.
3. Run `pytest` and ensure `docker build ...` still succeeds.
4. Open a pull request with context on the heuristics or UX you’re improving.

Bug fixes, new signal ideas, and registry adapters are especially appreciated.

---

## 📄 License

Released under the [MIT License](LICENSE) © Usman.
