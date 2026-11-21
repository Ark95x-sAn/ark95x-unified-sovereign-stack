export type CallMode = "voice" | "video";
export type CallState = "idle" | "calling" | "incoming" | "connected" | "ended" | "error";
export type PeerKind = "none" | "real-two-tab" | "simulated";

export interface Contact {
  id: string;
  name: string;
  handle: string;
  initials: string;
  color: string;
  online: boolean;
}

export interface Message {
  id: string;
  conversationId: string;
  author: "me" | "them";
  text: string;
  time: string;
}

export interface Conversation {
  id: string;
  contact: Contact;
  preview: string;
  time: string;
  unread: number;
}
