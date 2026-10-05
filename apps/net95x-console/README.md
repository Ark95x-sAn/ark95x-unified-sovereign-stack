# Net95X Console · fixture prototype

A browser-only React Native Web interface for the Network‑95 operations design. It demonstrates **Command → Queue → Proof → Agency → Review** on the GM700, Surface Pro X, or a phone browser.

Navigation is local screen state for the fixture: there are no deep links or browser back-stack routes. The HTML shell uses browser safe-area insets to keep the phone layout clear of system bars.

## Run

From this directory, use Node 24 or later:

```sh
npm ci
npm run web
```

Open `http://127.0.0.1:5173` on the machine running Vite. The development server binds to localhost only. For a static browser build, use `npm run build`; `npm run preview` serves it on localhost. `npm test` exercises the pure local mission guard and `npm run typecheck` checks the UI.

The Surface Pro X can use the built files through a separately configured local network server later. This prototype does not expose a network service by default.

The app imports React Native primitives, which Vite aliases to React Native Web. `src/react-native-web.d.ts` describes only the browser primitives this fixture uses; native mobile builds require their own toolchain and types.

## Walkthrough

1. **Command:** press the primary button to advance sample intake, indexing, routing, drafting, and the local guard.
2. **Queue:** inspect the one task and its two sample source records.
3. **Proof:** read the cited brief and ordered event log. The local guard checks required fields, known source IDs, and a source reference on each claim.
4. **Agency:** view proposed specialist lanes and devices 17 Surface Pro X, 16 RTX 2080 PC, and 15 GM700 in reverse order.
5. **Review:** after the guard passes, record a **simulated** review acknowledgement. Return to Proof for `SIM-RECEIPT-N95-DEMO-001`.

The six walkthrough stages are numbered **01–06**. Engineering dependency gates named C1–C6 elsewhere in Network‑95 are distinct.

## Boundaries

- The two fictional files in `fixtures/` are mirrored as bundled excerpts in `src/mission.ts`; the test checks they remain in sync. No account histories, case records, credentials, or actual business documents are imported.
- Provider adapters and three device connections are disconnected. “GM700,” “Surface,” and specialist actor labels describe intended placement, not observed execution.
- Drafting is deterministic sample content. The separate local guard is code in this prototype; a truly independent reviewer is future work.
- External sends are held, including the existing REV‑002 freeze. There is no network send path in the app.
- State is kept in memory and resets on reload. The receipt is a demo marker, not proof of a physical device connection, human signature, or submission.

## Source-linked handoff target

For the first real integration, replace the fixture with a user-supplied folder, preserve each original and source ID, route the draft to a connected worker, give an independent verifier the exact draft and sources, then request Surface review and retain a genuine receipt. The adapter must report disconnected, unknown, or failed states honestly.
