"use client";

import { useMemo, useState } from "react";
import type { FormEvent } from "react";
import { CONVERSATIONS, INITIAL_MESSAGES } from "../../lib/mock-data";
import type { CallMode, Message } from "../../lib/types";
import { useCall } from "../../hooks/useCall";
import CallScreen from "../../components/CallScreen";

export default function DmPage() {
  const [activeId, setActiveId] = useState(CONVERSATIONS[0].id);
  const [messages, setMessages] = useState<Message[]>(INITIAL_MESSAGES);
  const [draft, setDraft] = useState("");
  const [chooserOpen, setChooserOpen] = useState(false);
  const call = useCall();

  const active = useMemo(() => CONVERSATIONS.find((c) => c.id === activeId) ?? CONVERSATIONS[0], [activeId]);
  const thread = messages.filter((m) => m.conversationId === activeId);

  function sendMessage(e: FormEvent) {
    e.preventDefault();
    const text = draft.trim();
    if (!text) return;
    setMessages((prev) => [...prev, { id: `m-${Date.now()}`, conversationId: activeId, author: "me", text, time: new Date().toLocaleTimeString([], { hour: "numeric", minute: "2-digit" }) }]);
    setDraft("");
  }

  function choose(mode: CallMode) {
    setChooserOpen(false);
    void call.startCall(mode, activeId, active.contact.name);
  }

  const inCall = call.state === "calling" || call.state === "connected" || call.state === "ended";

  return (
    <main className="shell">
      <aside className="sidebar">
        <h1>Messages</h1>
        <p className="sample-banner">Sample data only — mock contacts, local state, no X login, nothing sent externally.</p>
        <p className="two-tab-tip">Two-tab real peer: open this page in a second tab, start a call here, accept there. Otherwise after 8s it connects to a clearly labeled simulated peer.</p>
        {CONVERSATIONS.map((c) => (
          <button key={c.id} type="button" className={`conv ${c.id === activeId ? "active" : ""}`} onClick={() => setActiveId(c.id)}>
            <span className="avatar" style={{ background: c.contact.color }}>{c.contact.initials}</span>
            <span className="conv-text"><strong>{c.contact.name}</strong><small>{c.preview}</small></span>
            <span className="conv-meta"><small>{c.time}</small>{c.unread > 0 && <b>{c.unread}</b>}</span>
          </button>
        ))}
      </aside>

      <section className="thread">
        <header className="thread-header">
          <span className="avatar" style={{ background: active.contact.color }}>{active.contact.initials}</span>
          <div><strong>{active.contact.name}</strong><small>{active.contact.handle} · {active.contact.online ? "Online (sample)" : "Offline (sample)"}</small></div>
          {/* Phone icon in thread header — modeled on X's DM flow */}
          <button type="button" className="phone-btn" aria-label="Start a call" title="Call — choose voice or video" onClick={() => setChooserOpen(true)}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z"/></svg>
          </button>
        </header>

        {call.incoming && (
          <div className="incoming" role="alert">
            <span>Incoming {call.incoming.mode} call from {call.incoming.fromName} (second tab)</span>
            <button type="button" onClick={() => void call.acceptIncoming()}>Accept</button>
            <button type="button" onClick={call.rejectIncoming}>Decline</button>
          </div>
        )}

        <div className="messages">
          {thread.map((m) => (<div key={m.id} className={`bubble ${m.author}`}><p>{m.text}</p><small>{m.time}</small></div>))}
        </div>

        <form className="composer" onSubmit={sendMessage}>
          <input value={draft} onChange={(e) => setDraft(e.target.value)} placeholder="Start a new message (local only)" aria-label="Message" />
          <button type="submit">Send</button>
        </form>
      </section>

      {chooserOpen && (
        <div className="chooser-overlay" role="dialog" aria-label="Choose call type" onClick={() => setChooserOpen(false)}>
          <div className="chooser" onClick={(e) => e.stopPropagation()}>
            <h2>Call {active.contact.name}?</h2>
            <p>Modeled on X: phone icon in a DM, then choose voice or video. This demo never calls a real X user.</p>
            <button type="button" onClick={() => choose("voice")}>🎙 Voice call — audio only</button>
            <button type="button" onClick={() => choose("video")}>📹 Video call — camera + audio</button>
            <button type="button" className="cancel" onClick={() => setChooserOpen(false)}>Cancel</button>
          </div>
        </div>
      )}

      {inCall && (
        <CallScreen state={call.state} mode={call.mode} peerKind={call.peerKind} contactName={active.contact.name} contactInitials={active.contact.initials}
          formatted={call.formatted} micLevel={call.micLevel} muted={call.muted} cameraOn={call.cameraOn} error={call.error}
          localStream={call.localStream} remoteStream={call.remoteStream}
          onMute={call.toggleMute} onCamera={call.toggleCamera} onEnd={() => call.endCall()} onClose={call.reset} />
      )}
    </main>
  );
}
