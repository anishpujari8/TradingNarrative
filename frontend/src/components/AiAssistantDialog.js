import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Wand2, Loader2, Copy, Replace, ListPlus } from "lucide-react";
import { toast } from "sonner";
import { streamAi } from "@/lib/aiStream";

const MODES = [
  { key: "draft", label: "Draft from notes", hint: "Give the assistant a brief or rough notes — it writes a full draft in your voice." },
  { key: "polish", label: "Polish current draft", hint: "Tightens grammar, clarity and flow while keeping your structure and voice." },
  { key: "expand", label: "Expand current draft", hint: "Deepens the argument with examples and mechanics, keeping your structure." },
];

export const AiAssistantDialog = ({ open, onOpenChange, content, onReplace, onAppend }) => {
  const [mode, setMode] = useState("draft");
  const [notes, setNotes] = useState("");
  const [output, setOutput] = useState("");
  const [busy, setBusy] = useState(false);

  const modeInfo = MODES.find((m) => m.key === mode);
  const paragraphs = content ? content.split(/\n\s*\n/).filter((b) => b.trim()).length : 0;

  const generate = async () => {
    if (mode === "draft" && !notes.trim()) {
      toast.error("Add a brief or some notes for the draft.");
      return;
    }
    if (mode !== "draft" && !content?.trim()) {
      toast.error("Your draft is empty — write something to polish or expand first.");
      return;
    }
    setBusy(true);
    setOutput("");
    try {
      const body = mode === "draft"
        ? { mode, text: notes.trim() }
        : { mode, text: content, instructions: notes.trim() || undefined };
      await streamAi("/admin/ai/assist", body, {
        onDelta: (d) => setOutput((o) => o + d),
      });
    } catch (err) {
      toast.error(err.message || "Generation failed. Try again.");
    } finally {
      setBusy(false);
    }
  };

  const copyOutput = async () => {
    try {
      await navigator.clipboard.writeText(output);
      toast.success("Copied to clipboard.");
    } catch {
      toast.error("Copy failed.");
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-2xl max-h-[90vh] overflow-y-auto" data-testid="ai-assistant-dialog">
        <DialogHeader>
          <DialogTitle className="font-serif text-2xl flex items-center gap-2">
            <Wand2 className="h-5 w-5 text-accent" /> AI writing assistant
          </DialogTitle>
          <DialogDescription>Gemini-powered drafting in your editorial voice. Review everything before publishing.</DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label>Action</Label>
              <Select value={mode} onValueChange={setMode}>
                <SelectTrigger data-testid="ai-assistant-mode-select"><SelectValue /></SelectTrigger>
                <SelectContent>
                  {MODES.map((m) => <SelectItem key={m.key} value={m.key}>{m.label}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div className="text-xs text-muted-foreground self-end pb-2">
              {mode === "draft" ? modeInfo.hint : `${modeInfo.hint} Uses your current draft (${paragraphs} paragraphs).`}
            </div>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="ai-notes">{mode === "draft" ? "Brief / notes for the draft" : "Extra instructions (optional)"}</Label>
            <Textarea
              id="ai-notes"
              rows={mode === "draft" ? 5 : 2}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder={mode === "draft"
                ? "e.g. Why demurrage clocks start before the paperwork does — cover laytime, NOR, and the 3 disputes every desk sees…"
                : "e.g. Make the opening punchier, keep it under 800 words…"}
              data-testid="ai-assistant-notes-input"
            />
          </div>

          <Button onClick={generate} disabled={busy} className="bg-accent text-accent-foreground hover:bg-accent/90 w-full" data-testid="ai-assistant-generate-button">
            {busy ? (<><Loader2 className="h-4 w-4 mr-2 animate-spin" /> Writing…</>) : (<><Wand2 className="h-4 w-4 mr-2" /> Generate</>)}
          </Button>

          {(output || busy) && (
            <div className="space-y-3">
              <div
                className="border border-border rounded-lg p-4 bg-muted/30 max-h-72 overflow-y-auto whitespace-pre-wrap font-serif text-sm leading-6"
                data-testid="ai-assistant-output"
              >
                {output || "Thinking…"}
              </div>
              {output && !busy && (
                <div className="flex flex-wrap gap-2">
                  <Button variant="outline" size="sm" onClick={() => { onReplace(output); onOpenChange(false); toast.success("Draft replaced with the generated text."); }} data-testid="ai-assistant-replace-button">
                    <Replace className="h-4 w-4 mr-2" /> Replace draft
                  </Button>
                  <Button variant="outline" size="sm" onClick={() => { onAppend(output); onOpenChange(false); toast.success("Generated text appended to your draft."); }} data-testid="ai-assistant-append-button">
                    <ListPlus className="h-4 w-4 mr-2" /> Append to draft
                  </Button>
                  <Button variant="ghost" size="sm" onClick={copyOutput} data-testid="ai-assistant-copy-button">
                    <Copy className="h-4 w-4 mr-2" /> Copy
                  </Button>
                </div>
              )}
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};
