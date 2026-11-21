import type { Conversation, Message } from "./types";

// SAMPLE DATA — mock contacts/messages only. No real X users, no X API.
export const CONVERSATIONS: Conversation[] = [
  { id: "c-maya", contact: { id: "maya", name: "Maya Chen (sample)", handle: "@maya_sample", initials: "MC", color: "#1d9bf0", online: true }, preview: "That clip idea sounds good — call?", time: "9:41 AM", unread: 2 },
  { id: "c-jordan", contact: { id: "jordan", name: "Jordan Lee (sample)", handle: "@jordan_sample", initials: "JL", color: "#7856ff", online: true }, preview: "Sent you the notes from yesterday", time: "8:15 AM", unread: 0 },
  { id: "c-sam", contact: { id: "sam", name: "Sam Rivera (sample)", handle: "@sam_sample", initials: "SR", color: "#00ba7c", online: false }, preview: "Let's sync tomorrow morning", time: "Yesterday", unread: 0 },
];

export const INITIAL_MESSAGES: Message[] = [
  { id: "m1", conversationId: "c-maya", author: "them", text: "Hey! Did you see the new DM calling flow on X? Phone icon right in the thread.", time: "9:38 AM" },
  { id: "m2", conversationId: "c-maya", author: "me", text: "Yeah — tap it and you choose voice or video. Building a local demo of that flow.", time: "9:39 AM" },
  { id: "m3", conversationId: "c-maya", author: "them", text: "Nice. This thread is sample data, so try the call button above whenever.", time: "9:41 AM" },
  { id: "m4", conversationId: "c-jordan", author: "them", text: "Sent you the notes from yesterday — all local, nothing external.", time: "8:15 AM" },
  { id: "m5", conversationId: "c-sam", author: "them", text: "Let's sync tomorrow morning. Sample conversation only.", time: "Yesterday" },
];

export function peerLabel(kind: string): string {
  switch (kind) {
    case "real-two-tab":
      return "REAL PEER — second tab (WebRTC, BroadcastChannel signaling)";
    case "simulated":
      return "SIMULATED PEER — demo only, no person is connected";
    case "none":
      return "No peer yet";
    default: {
      const _exhaustive: never = kind as never;
      return _exhaustive;
    }
  }
}
