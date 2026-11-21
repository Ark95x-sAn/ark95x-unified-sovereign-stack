import { useCallback, useEffect, useRef, useState } from "react";
import type { CallMode, CallState, PeerKind } from "../lib/types";

const CHANNEL = "jarvis-dm-call-v1";
type Signal =
  | { type: "invite"; callId: string; mode: CallMode; conversationId: string; fromName: string }
  | { type: "accept"; callId: string }
  | { type: "reject"; callId: string }
  | { type: "end"; callId: string }
  | { type: "offer"; callId: string; sdp: RTCSessionDescriptionInit }
  | { type: "answer"; callId: string; sdp: RTCSessionDescriptionInit }
  | { type: "ice"; callId: string; candidate: RTCIceCandidateInit };

export interface Incoming { callId: string; mode: CallMode; conversationId: string; fromName: string }

function format(sec: number) {
  return `${String(Math.floor(sec / 60)).padStart(2, "0")}:${String(sec % 60).padStart(2, "0")}`;
}

export function useCall(onRemoteEnded?: () => void) {
  const [state, setState] = useState<CallState>("idle");
  const [mode, setMode] = useState<CallMode>("voice");
  const [peerKind, setPeerKind] = useState<PeerKind>("none");
  const [muted, setMuted] = useState(false);
  const [cameraOn, setCameraOn] = useState(true);
  const [seconds, setSeconds] = useState(0);
  const [micLevel, setMicLevel] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [incoming, setIncoming] = useState<Incoming | null>(null);

  const bcRef = useRef<BroadcastChannel | null>(null);
  const pcRef = useRef<RTCPeerConnection | null>(null);
  const localRef = useRef<MediaStream | null>(null);
  const remoteRef = useRef<MediaStream | null>(null);
  const callIdRef = useRef<string>("");
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const stateRef = useRef<CallState>("idle");
  stateRef.current = state;

  const [localStream, setLocalStream] = useState<MediaStream | null>(null);
  const [remoteStream, setRemoteStream] = useState<MediaStream | null>(null);

  const send = useCallback((msg: Signal) => bcRef.current?.postMessage(msg), []);

  const cleanupMedia = useCallback(() => {
    localRef.current?.getTracks().forEach((t) => t.stop());
    localRef.current = null;
    setLocalStream(null);
    pcRef.current?.close();
    pcRef.current = null;
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
  }, []);

  const endCall = useCallback((notify = true) => {
    if (notify && callIdRef.current) send({ type: "end", callId: callIdRef.current });
    cleanupMedia();
    setState("ended");
    setIncoming(null);
  }, [cleanupMedia, send]);

  const startTimerReset = useCallback(() => { setSeconds(0); setMuted(false); setCameraOn(true); setError(null); }, []);

  const getMedia = useCallback(async (m: CallMode) => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: m === "video" });
      localRef.current = stream;
      setLocalStream(stream);
      return stream;
    } catch {
      setError("Microphone/camera permission denied or unavailable. You can still view the simulated-peer demo — no local media is captured.");
      return null;
    }
  }, []);

  const createPc = useCallback((callId: string) => {
    const pc = new RTCPeerConnection({ iceServers: [{ urls: "stun:stun.l.google.com:19302" }] });
    pcRef.current = pc;
    localRef.current?.getTracks().forEach((t) => pc.addTrack(t, localRef.current!));
    pc.ontrack = (e) => {
      const s = e.streams[0] ?? new MediaStream([e.track]);
      remoteRef.current = s;
      setRemoteStream(s);
    };
    pc.onicecandidate = (e) => { if (e.candidate) send({ type: "ice", callId, candidate: e.candidate.toJSON() }); };
    pc.onconnectionstatechange = () => { if (pc.connectionState === "connected") { if (timeoutRef.current) clearTimeout(timeoutRef.current); setPeerKind("real-two-tab"); setState("connected"); } };
    return pc;
  }, [send]);

  // BroadcastChannel signaling — real two-tab peer, fallback to clearly-labeled simulated peer
  useEffect(() => {
    if (typeof BroadcastChannel === "undefined") return;
    const bc = new BroadcastChannel(CHANNEL);
    bcRef.current = bc;
    bc.onmessage = async (ev: MessageEvent<Signal>) => {
      const msg = ev.data;
      if (!msg || typeof msg !== "object") return;
      switch (msg.type) {
        case "invite":
          if (stateRef.current === "idle" || stateRef.current === "ended") setIncoming({ callId: msg.callId, mode: msg.mode, conversationId: msg.conversationId, fromName: msg.fromName });
          break;
        case "accept": {
          if (msg.callId !== callIdRef.current || stateRef.current !== "calling") break;
          if (timeoutRef.current) clearTimeout(timeoutRef.current);
          setPeerKind("real-two-tab");
          const pc = createPc(msg.callId);
          const offer = await pc.createOffer();
          await pc.setLocalDescription(offer);
          send({ type: "offer", callId: msg.callId, sdp: offer });
          break;
        }
        case "reject":
          if (msg.callId === callIdRef.current) { cleanupMedia(); setState("ended"); }
          break;
        case "end":
          if (msg.callId === callIdRef.current || (incoming && msg.callId === incoming.callId)) { cleanupMedia(); setIncoming(null); setState("ended"); onRemoteEnded?.(); }
          break;
        case "offer": {
          if (msg.callId !== callIdRef.current) break;
          const pc = pcRef.current ?? createPc(msg.callId);
          await pc.setRemoteDescription(msg.sdp);
          const answer = await pc.createAnswer();
          await pc.setLocalDescription(answer);
          send({ type: "answer", callId: msg.callId, sdp: answer });
          setPeerKind("real-two-tab");
          setState("connected");
          break;
        }
        case "answer":
          if (msg.callId === callIdRef.current) await pcRef.current?.setRemoteDescription(msg.sdp);
          break;
        case "ice":
          if (msg.callId === callIdRef.current && pcRef.current) { try { await pcRef.current.addIceCandidate(msg.candidate); } catch { /* late candidate */ } }
          break;
        default: {
          const _exhaustive: never = msg;
          void _exhaustive;
        }
      }
    };
    return () => bc.close();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // duration timer
  useEffect(() => {
    if (state !== "connected") return;
    const id = setInterval(() => setSeconds((s) => s + 1), 1000);
    return () => clearInterval(id);
  }, [state]);

  // mic level
  useEffect(() => {
    if (!localStream) { setMicLevel(0); return; }
    let raf = 0;
    let ctx: AudioContext | null = null;
    try {
      ctx = new AudioContext();
      const src = ctx.createMediaStreamSource(localStream);
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 256;
      src.connect(analyser);
      const data = new Uint8Array(analyser.frequencyBinCount);
      const tick = () => { analyser.getByteFrequencyData(data); setMicLevel(Math.min(1, data.reduce((a, b) => a + b, 0) / data.length / 128)); raf = requestAnimationFrame(tick); };
      tick();
    } catch { setMicLevel(0); }
    return () => { cancelAnimationFrame(raf); ctx?.close().catch(() => undefined); };
  }, [localStream]);

  const startCall = useCallback(async (m: CallMode, conversationId: string, contactName: string) => {
    startTimerReset();
    setMode(m);
    setPeerKind("none");
    const callId = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    callIdRef.current = callId;
    setState("calling");
    await getMedia(m);
    send({ type: "invite", callId, mode: m, conversationId, fromName: contactName });
    // No second tab answered in 8s -> simulated peer (honestly labeled everywhere in UI)
    timeoutRef.current = setTimeout(() => {
      if (stateRef.current === "calling") { setPeerKind("simulated"); setState("connected"); }
    }, 8000);
  }, [getMedia, send, startTimerReset]);

  const acceptIncoming = useCallback(async () => {
    if (!incoming) return;
    startTimerReset();
    setMode(incoming.mode);
    callIdRef.current = incoming.callId;
    await getMedia(incoming.mode);
    createPc(incoming.callId);
    setPeerKind("real-two-tab");
    send({ type: "accept", callId: incoming.callId });
    setIncoming(null);
    setState("connected");
  }, [createPc, getMedia, incoming, send, startTimerReset]);

  const rejectIncoming = useCallback(() => { if (incoming) send({ type: "reject", callId: incoming.callId }); setIncoming(null); }, [incoming, send]);

  const toggleMute = useCallback(() => {
    setMuted((prev) => { localRef.current?.getAudioTracks().forEach((t) => (t.enabled = prev)); return !prev; });
  }, []);
  const toggleCamera = useCallback(() => {
    setCameraOn((prev) => { localRef.current?.getVideoTracks().forEach((t) => (t.enabled = prev)); return !prev; });
  }, []);
  const reset = useCallback(() => { cleanupMedia(); setState("idle"); setPeerKind("none"); setSeconds(0); }, [cleanupMedia]);

  return { state, mode, peerKind, muted, cameraOn, seconds, formatted: format(seconds), micLevel, error, incoming, localStream, remoteStream, startCall, acceptIncoming, rejectIncoming, endCall, toggleMute, toggleCamera, reset };
}
