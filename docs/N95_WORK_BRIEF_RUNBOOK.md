# Local work brief: Windows handoff

This workflow turns one small folder of text notes into a dated work brief and source-linked task records. It runs once on one computer using an existing Python 3.11 or newer. It uses local rules and explicit task markers; no AI model, subscription, internet connection, account, or background service is required.

The $100 offer is a proposed fixed installation-and-handoff service for this one workflow. It includes up to 60 minutes of initial setup and acceptance, plus one support visit of up to 15 minutes within seven days: 75 provider minutes total. Payment, customer acceptance, and value delivered are not established by this document or a successful test.

## What the customer receives

- A reviewed portable folder containing `n95_workflow/`, `tools/N95-Work-Brief.ps1`, this guide, and the applicable license file. The large historical stack is unnecessary for this workflow.
- A configured command using the customer's actual Python, input, and output paths.
- A successful run on agreed notes, with `brief.md`, `observations.json`, and `manifest.json` in a content-identified output folder.
- A repeat-run demonstration, stop/retry instructions, and the ability to keep or export all local files.

No system software is installed. If there is no runnable Python 3.11+ or local policy prevents the reviewed script from running, this computer does not yet meet this offer's prerequisites. Do not promise a completed installation until the actual computer passes and the customer can run the workflow.

## Prepare three separate local folders

The examples use these locations. They are examples, not evidence that these folders exist on a customer's device.

| Purpose | Example |
|---|---|
| Reviewed portable program | `C:\Network95\work-brief` |
| Customer's source notes | `C:\WorkNotes\input` |
| Generated output | `C:\WorkNotes\output` |

Input and output must not overlap. Output must be outside the portable program folder and every Git checkout. Use normal local folders; network shares, mapped network drives, links, junctions, and other reparse points are outside this small service's scope. The workflow does not recurse into subfolders.

Put 1 to 50 ordinary `.txt` or `.md` files in the input folder, totaling at most 1 MiB. Remove unrelated files from the selected input folder yourself or choose a dedicated notes folder. Nested folders and unsupported entries are rejected rather than silently skipped. Use UTF-8 text files. PDFs, Word documents, spreadsheets, browser exports with folders, and cloud-only placeholder files need a separate preparation step and are not part of this offer.

Write actionable items explicitly:

```text
- [ ] Confirm the delivery time [id:JOB1] [due:2026-09-10] [owner:Ben]
- [ ] Check the supply count [id:JOB2]
- [x] Write the meeting notes [id:JOB3]
```

`- [ ]` marks an open task; `- [x]` and `- [X]` mark completed items. Optional metadata uses `[id:...]`, `[due:YYYY-MM-DD]`, and `[owner:...]`. Ordinary prose remains source context and is not automatically treated as an instruction to execute. The tool extracts and reports; it never completes the tasks on the customer's behalf.

## Check this computer before the first run

Use a normal Windows PowerShell terminal. The provider fills in the real, already installed `python.exe` path and validates it. `py.exe`, Microsoft Store aliases, and automatic Python installation are not used. No admin access, package installation, or PATH change is required.

For example, if the direct interpreter already exists at `C:\Python311\python.exe`:

```powershell
powershell.exe -NoProfile -File "C:\Network95\work-brief\tools\N95-Work-Brief.ps1" -PythonExecutable "C:\Python311\python.exe" -InputDirectory "C:\WorkNotes\input" -OutputDirectory "C:\WorkNotes\output" -AsOf "2026-09-10" -CheckOnly
$LASTEXITCODE
```

`-CheckOnly` prints a JSON prerequisite result and creates no workflow output. It checks the runnable Python version, portable module, input inventory, folder separation, and date. A result with `passed: true` and exit code `0` permits the first real run. Exit code `2` means one or more prerequisites are missing or unverified. The output lists failed checks. A prerequisite pass does not prove that the source contents parse or that an output can be written.

No PowerShell runtime is available in the current Linux build environment. This wrapper has been statically reviewed but has not been parsed or executed on Windows here. Hosted or physical Windows verification must be recorded separately; no physical customer deployment is verified by this guide.

## Run and read the result

Remove `-CheckOnly` and choose the date used to evaluate the brief:

```powershell
powershell.exe -NoProfile -File "C:\Network95\work-brief\tools\N95-Work-Brief.ps1" -PythonExecutable "C:\Python311\python.exe" -InputDirectory "C:\WorkNotes\input" -OutputDirectory "C:\WorkNotes\output" -AsOf "2026-09-10"
$LASTEXITCODE
```

The wrapper invokes the agreed module interface:

```text
python -m n95_workflow run --input PATH --output PATH --as-of YYYY-MM-DD
```

The result identifies an output folder below the chosen output parent. Its full content identifier names a folder containing:

| File | Use |
|---|---|
| `brief.md` | Readable brief and source references; open in a text or Markdown viewer. |
| `observations.json` | Structured extracted information, including task/source records. |
| `manifest.json` | Run information and integrity evidence used to verify repeat runs. |

Keep all three together. Compare at least one task, its due date/owner, and its source reference with the original note before accepting the delivery. This comparison is part of proving the workflow's usefulness, even when the software reports success.

Running the same named input files and bytes with the same date, settings, and implementation verifies and reuses the existing result. Changes to inputs, filenames, date, context settings, or implementation produce a different content identifier. Existing output must pass verification before it can be reused; a folder existing by itself does not prove success. The portable wrapper uses the default context setting.

## Stop, recover, and retry

Press **Ctrl+C** in the running terminal to stop a foreground run. There is no background watcher, service, or scheduled task to stop afterward. An interrupted or failed command is not a completed delivery.

After failure, read the reported issue, correct the selected input or folder path, and run `-CheckOnly` again. Then rerun the same command. Do not delete existing output to make a failed integrity check disappear. Preserve a questioned result for review and use a fresh separate output folder when a clean retry is needed. The workflow's content checks and atomic final output determine whether an existing result is reusable.

If Windows blocks the script, record the block and inspect the reviewed script and local execution policy. This guide contains no bypass or unblocking command. A policy block is an unresolved prerequisite, not a successful installation.

## Customer acceptance and the 75-minute limit

| Provider time | Concrete acceptance work |
|---|---|
| First 10 minutes | Confirm one supported computer, existing Python, agreed folder, and file limits. Stop the fixed offer if these do not fit. |
| Next 15 minutes | Place the reviewed portable package, configure actual paths, and pass `-CheckOnly`. |
| Next 20 minutes | Run agreed notes, compare task/source output, and demonstrate a repeat run. |
| Final 15 initial minutes | Customer runs it without assistance; record stop/retry/export instructions and unresolved limits. |
| Up to 15 support minutes within seven days | One focused troubleshooting or handoff follow-up for the same workflow. |

Accept only after the customer can generate and locate the brief, verify an extracted item against its source, repeat the run, and explain how to stop and retry. Record the actual installation time and acceptance result. Extra integrations, document conversion, Python installation, model setup, multiple computers, recurring maintenance, and additional support require a separate scope; they are not hidden promises within the $100 offer.

## Files, export, and removal

Source notes and generated results stay on the customer's computer. The customer chooses when and with whom to share them. Copying the output folder exports readable Markdown and JSON; keep the manifest with it. Source notes remain separate and are read without intentional modification. Retain the program's license when copying the program itself.

To remove the workflow, close any foreground run and manually remove only the portable program folder when ready. There is no service, account, registry entry, or scheduled task installed by this runner. Keep source notes and output folders until the customer separately decides what to retain. This guide supplies no automatic delete command, and uninstalling this workflow does not uninstall Python.
