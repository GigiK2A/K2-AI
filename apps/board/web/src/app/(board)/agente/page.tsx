import { requireUser } from "@/lib/auth";
import { apiFetch, ApiError } from "@/lib/api";
import type {
  AgentConversationDetail,
  AgentConversationListResponse,
  AgentContentBlock,
  ChatItem,
} from "@/types/agent";
import { BriefCard } from "@/components/agente/brief-card";
import { ChatShell } from "@/components/agente/chat-shell";
import { ConversationsSidebar } from "@/components/agente/conversations-sidebar";

interface BriefMemo {
  id: string;
  subject: string;
  body: string;
  tags: string[] | null;
  created_at: string;
}

async function safeLatestBrief(): Promise<BriefMemo | null> {
  try {
    const resp = await apiFetch<{ memo: BriefMemo | null }>("/api/agent/brief/latest");
    return resp.memo ?? null;
  } catch (err) {
    if (err instanceof ApiError && (err.status === 404 || err.status === 500)) {
      return null;
    }
    return null;
  }
}

export const dynamic = "force-dynamic";

interface AgentePageProps {
  searchParams: Promise<{ c?: string }>;
}

function blocksToText(blocks: AgentContentBlock[]): string {
  return blocks
    .filter((b): b is Extract<AgentContentBlock, { type: "text" }> => b.type === "text")
    .map(b => b.text)
    .join("");
}

function parseToolResultArgs(content: string): Record<string, unknown> | undefined {
  try {
    const parsed = JSON.parse(content);
    return typeof parsed === "object" && parsed !== null ? (parsed as Record<string, unknown>) : undefined;
  } catch {
    return undefined;
  }
}

/**
 * Rebuild flat ChatItem list from persisted Anthropic messages.
 * - assistant text/tool_use blocks render as assistant + tool cards
 * - subsequent user.content with tool_result blocks fills the tool result
 */
function reconstructItems(messages: AgentConversationDetail["messages"]): ChatItem[] {
  const items: ChatItem[] = [];
  const toolById = new Map<string, Extract<ChatItem, { kind: "tool" }>>();
  let counter = 0;
  const id = () => `r-${++counter}`;

  for (const msg of messages) {
    if (msg.role === "user") {
      if (typeof msg.content === "string") {
        items.push({ kind: "user", id: id(), text: msg.content });
      } else {
        // Tool result message — fill prior tool cards
        for (const block of msg.content) {
          if (block.type === "tool_result") {
            const card = toolById.get(block.tool_use_id);
            if (card) {
              const parsed = parseToolResultArgs(block.content);
              card.result = parsed;
              const isErr = parsed && typeof parsed.error === "string";
              card.status = isErr ? "error" : "done";
            }
          }
        }
      }
    } else {
      // assistant
      const text = blocksToText(msg.content);
      if (text) items.push({ kind: "assistant", id: id(), text });
      for (const block of msg.content) {
        if (block.type === "tool_use") {
          const card: Extract<ChatItem, { kind: "tool" }> = {
            kind: "tool",
            id: block.id,
            name: block.name,
            args: block.input,
            status: "done",
          };
          items.push(card);
          toolById.set(block.id, card);
        }
      }
    }
  }
  return items;
}

async function safeList(): Promise<AgentConversationListResponse> {
  try {
    return await apiFetch<AgentConversationListResponse>("/api/agent/conversations");
  } catch (err) {
    // Migration may not be applied yet — degrade gracefully.
    if (err instanceof ApiError && (err.status === 404 || err.status === 500)) {
      return { conversations: [] };
    }
    throw err;
  }
}

async function safeDetail(id: string): Promise<AgentConversationDetail | null> {
  try {
    return await apiFetch<AgentConversationDetail>(`/api/agent/conversations/${id}`);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) return null;
    throw err;
  }
}

export default async function AgentePage({ searchParams }: AgentePageProps) {
  await requireUser();
  const { c } = await searchParams;

  const [listResp, latestBrief] = await Promise.all([
    safeList(),
    safeLatestBrief(),
  ]);
  const conversations = listResp.conversations.slice(0, 10);

  let initialItems: ChatItem[] = [];
  let initialConversationId: string | undefined = undefined;
  if (c) {
    const detail = await safeDetail(c);
    if (detail) {
      initialConversationId = detail.id;
      initialItems = reconstructItems(detail.messages);
    }
  }

  return (
    <div className="flex h-[calc(100vh-3.5rem)] flex-col px-4 md:px-6 lg:px-8 pt-4">
      <header className="mb-3 flex flex-col gap-1">
        <h1 className="font-display text-2xl md:text-3xl">Giuseppina</h1>
        <p className="text-sm text-[color:var(--color-text-soft)]">
          Assistente operativa con accesso ai dati del board. Le scritture
          passano da te in <span className="text-[color:var(--color-teal)]">/approvazioni</span>.
        </p>
      </header>
      <div className="flex flex-1 min-h-0 gap-4">
        <ConversationsSidebar conversations={conversations} activeId={initialConversationId} />
        <div className="flex-1 min-w-0 mx-auto w-full max-w-3xl flex flex-col">
          <BriefCard memo={latestBrief} />
          <div className="flex-1 min-h-0">
            <ChatShell
              initialConversationId={initialConversationId}
              initialItems={initialItems}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
