# Daily Work Brief — $100 installation candidate

**Evaluation candidate. Customer value and physical installation are not yet proved. Do not market a measured-savings or AI-autonomy claim from this document.**

## One customer, one result

For a solo service operator or small-team coordinator who already keeps structured job notes in local text files: gather explicit open tasks, completed items, stated dates/owners and conflicts into one source-linked brief. The customer must already find gathering that information repeatedly burdensome. A customer with only a few notes or an adequate existing checklist may get better value from free existing tools.

1. The customer chooses one dedicated local folder containing 1–50 UTF-8 `.txt`/`.md` files, at most 1 MiB total and 10,000 extracted task occurrences.
2. A finite run extracts explicit checkbox lines and optional `[id:...]`, `[due:YYYY-MM-DD]`, `[owner:...]` fields. It preserves ambiguity and links observations to filenames, line numbers and source hashes.
3. The customer reads the brief, checks disputed entries against originals and chooses the next action. The program does not execute those actions.

The current implementation is deterministic extraction. No AI inference is included or claimed. The earlier $100 design assumed an existing local model; this narrower evaluation candidate removes that unproved dependency. It does not claim to understand arbitrary prose, OCR images, PDFs, spreadsheets, health signals or a three-device system. Formatting and source preparation are real customer costs and must be measured.

## Proposed installed service

| Item | Scope |
|---|---|
| Price | $100 once, for installation/configuration, validation, handoff and the defined support allowance |
| Software | MIT-licensed code, available free; the service fee is not a mandatory software license or subscription |
| Computer | One compatible computer with an existing working Python 3.11+; native customer compatibility must pass first |
| Connection | One selected local folder; manual run |
| Output | Readable brief, structured observations and integrity manifest; customer retains all three |
| Initial service | At most 60 provider minutes for preflight, setup, acceptance and handoff |
| Support | Up to 15 additional provider minutes within seven days for this same workflow; total cap 75 minutes |
| Extra costs | No required paid API/model/subscription; existing computer, Python, viewer and local storage remain prerequisites. Electricity and customer time still count. |
| Ownership and exit | Sources remain unchanged; portable files can be retained/exported; no installed watcher, account or subscription |

This is a draft offer for evaluation, not a launched service or an agreement with a customer. Proposed customer protection: a no-charge pilot; no installation fee if the agreed functional acceptance cannot be met. Any eventual terms need to be made concrete before a sale. A provider overrun must not create an undisclosed extra fee.

## Functional acceptance, before commercial claims

Require: actual supported input parsed; exact source references; conflicts preserved; no-ID notes not merged as known identities; unchanged source bytes; safe repeated output; tampered output rejected; disallowed paths/files fail visibly; operator can run, find results, stop and retry. Run the purchased workflow on the actual customer endpoint. Hosted CI can support portability; it is not customer acceptance.

Directories and the Python/program installation must be controlled by the customer/provider and stable during runs. Repeated path checks and no-follow protections do not establish resistance to a privileged or concurrent attacker who can replace ancestor directories. Windows ACL protection and physical installation need target evidence.

## Compare against the best free alternative

Use the customer's existing editor search, consolidated checklist or spreadsheet for the same task and quality target. Pick the most efficient adequate free baseline after a warm-up. Do not compare against an artificially inefficient manual process. If the free alternative wins, recommend it.

Predeclare at least ten representative paired jobs before timing; counterbalance the order and avoid reusing memorized content. Include every attempted run and fallback. For each pair, record the best free alternative's total time and this workflow's total time, including collection, reformatting, running, reviewing, correcting, retries and job-specific support. Source fidelity and task quality must meet the same agreed target. Keep recordings/timing records and the customer's acceptance private.

Then subtract one-time customer setup, additional support, nonoverlapping evaluation time and extra cash costs. No double-counting of time already included per job. Evaluate the customer's chosen value per hour; dollar-valued time is not demonstrated cash savings or revenue. Ten pairs alone do not establish a month of use or generalize to every customer.

The included calculator verifies supplied arithmetic and gate fields only:

```sh
python tools/n95_value_check.py docs/N95_VALUE_OBSERVATIONS_TEMPLATE.json
```

The blank template must return `INSUFFICIENT_EVIDENCE` and exit 1. It must never turn a synthetic fixture, missing comparison, failed quality check, unverified installation, omitted attempts or nine AI opinions into customer proof. Even `REPORTED_TIME_VALUE_EXCEEDS_PRICE` means conditional arithmetic on supplied records; authenticity and customer-value proof flags remain false until reviewed outside the calculator.

**Release rule:** PROVE → REVIEW → RELEASE. Missing proof means HOLD. Technical checks, independent AI review and actual customer value are separate gates.
