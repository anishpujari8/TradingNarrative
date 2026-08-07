import { useEffect, useRef, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { MessagesSquare, Send, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { streamAi } from "@/lib/aiStream";

export const AskEssayWidget = ({ slug }) => {
  const [enabled, setEnabled] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    api.get("/ai/status").then((r) => setEnabled(!!r.data.enabled)).catch(() => setEnabled(false));
  }, []);

  useEffect(() => {
    setMessages([]);
    setInput("");
  }, [slug]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  const ask = async () => {
    const question = input.trim();
    if (!question || busy) return;
    setInput("");
    setBusy(true);
    const history = messages.slice(-6).map((m) => ({ role: m.role, text: m.text }));
    setMessages((ms) => [...ms, { role: "user", text: question }, { role: "assistant", text: "" }]);
    try {
      await streamAi(`/posts/${encodeURIComponent(slug)}/ask`, { question, history }, {
        onDelta: (d) => setMessages((ms) => {
          const next = [...ms];
          next[next.length - 1] = { ...next[next.length - 1], text: next[next.length - 1].text + d };
          return next;
        }),
      });
    } catch (err) {
      setMessages((ms) => {
        const next = [...ms];
        next[next.length - 1] = { role: "assistant", text: err.message || "Something went wrong — please try again.", error: true };
        return next;
      });
    } finally {
      setBusy(false);
    }
  };

  if (!enabled) return null;

  return (
    <Card className="rounded-2xl mt-12" data-testid="ask-essay-widget">
      <CardHeader className="pb-3">
        <CardTitle className="font-serif text-2xl flex items-center gap-2.5">
          <MessagesSquare className="h-5 w-5 text-accent" /> Ask this essay
        </CardTitle>
        <p className="text-sm text-muted-foreground">Questions answered from this essay only — no outside guessing.</p>
      </CardHeader>
      <CardContent>
        {messages.length > 0 && (
          <div ref={scrollRef} className="space-y-3 max-h-80 overflow-y-auto mb-4 pr-1" data-testid="ask-essay-messages">
            {messages.map((m, i) => (
              <div key={i} className={m.role === "user" ? "flex justify-end" : "flex justify-start"}>
                <div
                  className={
                    m.role === "user"
                      ? "bg-accent text-accent-foreground rounded-2xl rounded-br-sm px-4 py-2.5 max-w-[85%] text-sm leading-6"
                      : `bg-muted/60 rounded-2xl rounded-bl-sm px-4 py-2.5 max-w-[85%] text-sm leading-6 whitespace-pre-wrap ${m.error ? "text-destructive" : ""}`
                  }
                  data-testid={`ask-essay-message-${m.role}`}
                >
                  {m.text || (busy && i === messages.length - 1 ? "…" : "")}
                </div>
              </div>
            ))}
          </div>
        )}
        <form
          className="flex items-center gap-2"
          onSubmit={(e) => { e.preventDefault(); ask(); }}
        >
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value.slice(0, 500))}
            placeholder="e.g. What's the key takeaway?"
            disabled={busy}
            data-testid="ask-essay-input"
          />
          <Button type="submit" size="icon" disabled={busy || !input.trim()} className="bg-accent text-accent-foreground hover:bg-accent/90 shrink-0" aria-label="Ask" data-testid="ask-essay-send-button">
            {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
};
