# DM Calling — Next.js local demo

A local-first Next.js DM flow modeled on X's DM calling: conversation list → open thread → phone icon in the thread header → voice-or-video chooser → call screen. Sample/mock data only. No X credentials, no X API, no real X users, nothing sent externally.

## Run

```bash
cd apps/dm-calling
npm install
npm run dev        # http://localhost:3100  -> redirects to /dm
npm run build      # production build check
curl http://localhost:3100/api/health   # {"ok":true,"service":"dm-calling",...}
```

## How X's flow maps to this build

| X (per prior lookup, treated as model) | This build |
|---|---|
| DM conversation list | Left sidebar, mock conversations (`lib/mock-data.ts`, labeled sample) |
| Open a DM thread | Thread pane with bubbles, local-state composer |
| Phone icon inside the DM thread header | Phone SVG button in thread header |
| Tap phone → choose voice or video | Chooser sheet: "Voice call" / "Video call" |
| Voice call screen | Audio-only screen, mic level meter, mute, end, timer, states |
| Video call screen | Local camera PiP, mute, camera toggle, end, timer, states |

Call states: `calling → connected → ended` (+ incoming / permission-error surfaces).

## What is real vs stubbed

**Real**
- Local media: `getUserMedia` mic (voice) / mic+camera (video), local preview, live mic level via Web Audio `AnalyserNode`, mute/camera track toggles, call timer.
- Two-tab peer (when you use it): real `RTCPeerConnection` media between two tabs of this same app, signaled over `BroadcastChannel` (`jarvis-dm-call-v1`) — invite/accept/reject/end + SDP/ICE relay. STUN is Google's public STUN only for candidate gathering; no TURN, no media server.
- DM messages: React local state only.

**Stubbed / simulated (honestly labeled)**
- If no second tab accepts within 8s, the call connects to a **SIMULATED PEER — demo only, no person is connected** (amber badge). It is never presented as a real person.
- Accounts, contact presence, message history, persistence: mock/sample, in-memory.
- Signaling for any real multi-device use: not implemented (BroadcastChannel is same-browser only).

## Production would still need

- Signaling server (WebSocket) tied to authenticated identities; BroadcastChannel does not cross devices/browsers.
- TURN servers (STUN alone fails on symmetric NAT), plus media-quality / reconnection handling.
- Auth, contact graph, blocking/reporting, call notifications/push, encryption expectations, and persistence.
- X API: DM calls are a first-party X product surface (per prior lookup); there is no verified public X API for placing DM calls to X users, so a production "call X users" feature cannot be built on this demo — it would be a separate, own-network calling product. That limit was not re-verified live in this task (no X credentials used, per scope).
- Browser permission UX, iOS Safari `getUserMedia` quirks, and background-tab throttling tests.

## Jarvis classification (AGENTS.md)

- Layer: Tools / approved integrations + Dashboard / observability (local UI demo).
- Risk: Yellow — creates local files and a local dev service; no external sends, no secrets, placeholders only.
- Health check: `GET /api/health`.
