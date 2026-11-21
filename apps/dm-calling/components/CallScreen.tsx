import { useEffect, useRef } from "react";
import type { CallMode, CallState, PeerKind } from "../lib/types";
import { peerLabel } from "../lib/mock-data";

interface Props {
  state: CallState; mode: CallMode; peerKind: PeerKind; contactName: string; contactInitials: string;
  formatted: string; micLevel: number; muted: boolean; cameraOn: boolean; error: string | null;
  localStream: MediaStream | null; remoteStream: MediaStream | null;
  onMute: () => void; onCamera: () => void; onEnd: () => void; onClose: () => void;
}

export default function CallScreen(p: Props) {
  const localVideo = useRef<HTMLVideoElement>(null);
  const remoteVideo = useRef<HTMLVideoElement>(null);
  const remoteAudio = useRef<HTMLAudioElement>(null);
  useEffect(() => { if (localVideo.current && p.localStream) localVideo.current.srcObject = p.localStream; }, [p.localStream]);
  useEffect(() => { if (remoteVideo.current && p.remoteStream) remoteVideo.current.srcObject = p.remoteStream; }, [p.remoteStream]);
  useEffect(() => { if (remoteAudio.current && p.remoteStream) remoteAudio.current.srcObject = p.remoteStream; }, [p.remoteStream]);

  const isSim = p.peerKind === "simulated";
  return (
    <div className="call-overlay" role="dialog" aria-label="Call screen">
      <div className="call-card">
        <div className={`peer-badge ${isSim ? "sim" : p.peerKind === "real-two-tab" ? "real" : ""}`}>{peerLabel(p.peerKind)}</div>
        <p className="call-state">
          {p.state === "calling" && "Calling… waiting for a second tab to answer (8s, then simulated-peer demo)"}
          {p.state === "connected" && `Connected · ${p.formatted}`}
          {p.state === "ended" && "Call ended"}
          {p.state === "error" && "Call error"}
        </p>
        <h2>{p.contactName}</h2>
        <p className="call-mode">{p.mode === "video" ? "Video call" : "Voice call"} · local media only, no X account involved</p>

        {p.mode === "video" ? (
          <div className="video-wrap">
            {p.remoteStream ? <video ref={remoteVideo} autoPlay playsInline className="remote-video" /> : (
              <div className="remote-placeholder"><span>{p.contactInitials}</span><small>{isSim ? "Simulated peer — animated placeholder, not a person" : "Waiting for remote video…"}</small></div>
            )}
            <video ref={localVideo} autoPlay playsInline muted className="local-video" />
            {!p.cameraOn && <div className="camera-off">Camera off</div>}
          </div>
        ) : (
          <div className="voice-wrap">
            <div className="avatar-big">{p.contactInitials}</div>
            <div className="mic-meter" aria-label="Microphone level"><div style={{ width: `${Math.round(p.micLevel * 100)}%` }} /></div>
            <small>{p.localStream ? `Microphone level ${Math.round(p.micLevel * 100)}% (local only, not recorded/sent${isSim ? " to anyone" : ""})` : "No local microphone stream"}</small>
            {p.remoteStream && <audio ref={remoteAudio} autoPlay />}
          </div>
        )}
        {p.error && <p className="call-error">{p.error}</p>}

        <div className="call-controls">
          <button type="button" onClick={p.onMute}>{p.muted ? "Unmute" : "Mute"}</button>
          {p.mode === "video" && <button type="button" onClick={p.onCamera}>{p.cameraOn ? "Camera off" : "Camera on"}</button>}
          {p.state !== "ended" ? <button type="button" className="end-btn" onClick={p.onEnd}>End call</button> : <button type="button" onClick={p.onClose}>Close</button>}
        </div>
      </div>
    </div>
  );
}
