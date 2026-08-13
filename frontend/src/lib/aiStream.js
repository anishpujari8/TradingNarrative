import { API } from "@/lib/api";

/**
 * POST to a streaming AI endpoint and consume its SSE response.
 * Calls onDelta(text) for each streamed chunk. Resolves when the stream finishes.
 * Throws Error(message) on HTTP errors or in-stream error events.
 */
export async function streamAi(path, body, { onDelta, signal } = {}) {
  // Auth rides in the httpOnly session cookie; the legacy header covers
  // pre-cookie sessions until AuthContext migrates them.
  const token = localStorage.getItem("ttn_token");
  const res = await fetch(`${API}${path}`, {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(body),
    signal,
  });
  if (!res.ok) {
    let detail = "The assistant is temporarily unavailable. Please try again.";
    try {
      const data = await res.json();
      if (data?.detail) detail = data.detail;
    } catch { /* non-JSON error body */ }
    throw new Error(detail);
  }
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const events = buffer.split("\n\n");
    buffer = events.pop();
    for (const event of events) {
      const line = event.trim();
      if (!line.startsWith("data:")) continue;
      let payload;
      try {
        payload = JSON.parse(line.slice(5).trim());
      } catch {
        continue;
      }
      if (payload.error) throw new Error(payload.error);
      if (payload.delta) onDelta?.(payload.delta);
      if (payload.done) return;
    }
  }
}
