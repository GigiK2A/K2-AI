// Sprint 9A — Giuseppina agent client types.

export interface AgentConversationSummary {
  id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
}

export interface AgentConversationListResponse {
  conversations: AgentConversationSummary[];
}

export interface AgentConversationDetail extends AgentConversationSummary {
  messages: AgentStoredMessage[];
}

// Mirror of Anthropic message shape we persist.
export type AgentStoredMessage =
  | { role: "user"; content: string | AgentContentBlock[] }
  | { role: "assistant"; content: AgentContentBlock[] };

export type AgentContentBlock =
  | { type: "text"; text: string }
  | { type: "tool_use"; id: string; name: string; input: Record<string, unknown> }
  | { type: "tool_result"; tool_use_id: string; content: string };

// SSE event types streamed from /api/agent/chat
export type AgentSSEEvent =
  | { type: "conversation"; id: string }
  | { type: "text"; content: string }
  | { type: "tool_call"; id: string; name: string; args: Record<string, unknown> }
  | { type: "tool_result"; id: string; name: string; result: Record<string, unknown> }
  | { type: "final"; content: string }
  | { type: "done"; messages: AgentStoredMessage[] }
  | { type: "error"; message: string };

// UI render model — flat sequence of items in a chat thread.
export type ChatItem =
  | { kind: "user"; id: string; text: string }
  | { kind: "assistant"; id: string; text: string; streaming?: boolean }
  | {
      kind: "tool";
      id: string;
      name: string;
      args: Record<string, unknown>;
      result?: Record<string, unknown>;
      status: "running" | "done" | "error";
    };
