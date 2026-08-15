import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Skeleton } from "@/components/ui/skeleton";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from "@/components/ui/dialog";
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Crown, Megaphone, MessagesSquare, Plus, Send, Trash2, ArrowLeft, Lock, Pin, LockOpen, CalendarClock, Pencil, Activity, TrendingUp, TrendingDown, Lightbulb, ArrowRight } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "sonner";
import { Seo } from "@/components/Seo";
import { api, formatDate } from "@/lib/api";
import { pillarAccent, withAlpha, PillarMotif, pillarMascot, PILLAR_MASCOT_ALTS } from "@/lib/pillars";
import { useAuth } from "@/context/AuthContext";

const initials = (name) => (name || "M").slice(0, 2).toUpperCase();

const NARRATIVE_TAGS = [
  { value: "bullish", label: "Bullish", Icon: TrendingUp },
  { value: "bearish", label: "Bearish", Icon: TrendingDown },
  { value: "insight", label: "Insight", Icon: Lightbulb },
];
const REACTIONS = ["📈", "📉", "💡"];

const AuthorLine = ({ author, date, onProfile }) => (
  <div className="flex items-center gap-2">
    <button
      type="button"
      onClick={(e) => { e.stopPropagation(); onProfile?.(author); }}
      className="flex items-center gap-2 rounded-md hover:bg-muted/60 px-1 -mx-1 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
      data-testid={`community-author-${author?.id}`}
      aria-label={`View ${author?.name}'s profile`}
    >
      <Avatar className="h-6 w-6 border border-border">
        <AvatarFallback className="bg-secondary text-[10px] font-medium">{initials(author?.name)}</AvatarFallback>
      </Avatar>
      <span className="text-xs font-medium">{author?.name}</span>
    </button>
    {author?.role === "admin" && (
      <Badge className="bg-accent/10 text-accent border-accent/30 hover:bg-accent/10 text-[9px] px-1.5 py-0">Editor</Badge>
    )}
    <span className="text-[11px] text-muted-foreground font-mono">{formatDate(date)}</span>
  </div>
);

export default function CommunityPage() {
  const { user, loading } = useAuth();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const deepLinkDone = useRef(false);
  const isAdmin = user?.role === "admin";

  const [announcements, setAnnouncements] = useState(null);
  const [threads, setThreads] = useState(null);
  const [narrative, setNarrative] = useState(null); // editor's market takes
  const [drafts, setDrafts] = useState(null); // early-access scheduled posts
  const [takeForm, setTakeForm] = useState({ body: "", tag: "" });
  const [takeBusy, setTakeBusy] = useState(false);
  const [locked, setLocked] = useState(false);
  const [selected, setSelected] = useState(null); // {thread, replies}
  const [detailBusy, setDetailBusy] = useState(false);

  const [newThreadOpen, setNewThreadOpen] = useState(false);
  const [threadForm, setThreadForm] = useState({ title: "", body: "" });
  const [posting, setPosting] = useState(false);

  const [annOpen, setAnnOpen] = useState(false);
  const [annForm, setAnnForm] = useState({ title: "", body: "", publish_at: "" });
  const [annBusy, setAnnBusy] = useState(false);
  const [annEditing, setAnnEditing] = useState(null); // announcement id when editing

  const [profile, setProfile] = useState(null); // member profile data
  const [profileOpen, setProfileOpen] = useState(false);

  const [replyBody, setReplyBody] = useState("");
  const [replying, setReplying] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null); // {type, id}

  const loadLounge = useCallback(() => {
    api.get("/community/announcements")
      .then((r) => { setAnnouncements(r.data.announcements); setLocked(false); })
      .catch((err) => { if (err?.response?.status === 403) setLocked(true); setAnnouncements([]); });
    api.get("/community/threads")
      .then((r) => setThreads(r.data.threads))
      .catch(() => setThreads([]));
    api.get("/community/narrative")
      .then((r) => setNarrative(r.data.takes))
      .catch(() => setNarrative([]));
    api.get("/community/early-access")
      .then((r) => setDrafts(r.data.drafts))
      .catch(() => setDrafts([]));
  }, []);

  useEffect(() => {
    if (loading) return;
    if (!user) return;
    if (!user.is_premium && !isAdmin) { setLocked(true); return; }
    loadLounge();
  }, [user, loading, isAdmin, loadLounge]);

  // Deep-link: /lounge?thread=<id> (from bell notifications) opens the discussion
  useEffect(() => {
    const tid = searchParams.get("thread");
    if (!tid || deepLinkDone.current || loading || !user) return;
    if (!user.is_premium && !isAdmin) return;
    deepLinkDone.current = true;
    openThread(tid);
    setSearchParams({}, { replace: true });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams, loading, user, isAdmin]);

  const openThread = async (tid) => {
    setDetailBusy(true);
    try {
      const res = await api.get(`/community/threads/${tid}`);
      setSelected(res.data);
    } catch {
      toast.error("Could not open that discussion.");
    } finally {
      setDetailBusy(false);
    }
  };

  const openProfile = async (author) => {
    if (!author?.id) return;
    setProfile(null);
    setProfileOpen(true);
    try {
      const res = await api.get(`/community/members/${author.id}`);
      setProfile(res.data);
    } catch {
      setProfileOpen(false);
      toast.error("Could not load that member's profile.");
    }
  };

  const createThread = async () => {
    if (threadForm.title.trim().length < 3) { toast.error("Give your discussion a title (3+ characters)."); return; }
    if (!threadForm.body.trim()) { toast.error("Write something to start the discussion."); return; }
    setPosting(true);
    try {
      await api.post("/community/threads", threadForm);
      toast.success("Discussion started.");
      setNewThreadOpen(false);
      setThreadForm({ title: "", body: "" });
      loadLounge();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not start the discussion.");
    } finally {
      setPosting(false);
    }
  };

  const isoToLocalInput = (isoStr) => {
    if (!isoStr) return "";
    const d = new Date(isoStr);
    const pad = (n) => String(n).padStart(2, "0");
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
  };

  const openAnnEditor = (a = null) => {
    if (a) {
      setAnnEditing(a.id);
      setAnnForm({ title: a.title, body: a.body, publish_at: a.scheduled ? isoToLocalInput(a.publish_at) : "" });
    } else {
      setAnnEditing(null);
      setAnnForm({ title: "", body: "", publish_at: "" });
    }
    setAnnOpen(true);
  };

  const createAnnouncement = async () => {
    if (annForm.title.trim().length < 3) { toast.error("Announcement needs a title (3+ characters)."); return; }
    if (!annForm.body.trim()) { toast.error("Write the announcement body."); return; }
    setAnnBusy(true);
    try {
      const payload = { title: annForm.title, body: annForm.body };
      if (annForm.publish_at) payload.publish_at = new Date(annForm.publish_at).toISOString();
      const res = annEditing
        ? await api.put(`/community/announcements/${annEditing}`, payload)
        : await api.post("/community/announcements", payload);
      toast.success(
        annEditing
          ? res.data.scheduled ? "Announcement updated, rescheduled." : "Announcement updated."
          : res.data.scheduled ? "Announcement scheduled, it publishes automatically." : "Announcement posted."
      );
      setAnnOpen(false);
      setAnnEditing(null);
      setAnnForm({ title: "", body: "", publish_at: "" });
      loadLounge();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not save the announcement.");
    } finally {
      setAnnBusy(false);
    }
  };

  const postTake = async () => {
    if (takeForm.body.trim().length < 3) { toast.error("Write a little more than that."); return; }
    setTakeBusy(true);
    try {
      await api.post("/community/narrative", { body: takeForm.body, tag: takeForm.tag || null });
      toast.success("Take posted to the narrative feed.");
      setTakeForm({ body: "", tag: "" });
      loadLounge();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not post the take.");
    } finally {
      setTakeBusy(false);
    }
  };

  const reactToTake = async (nid, emoji) => {
    try {
      const res = await api.post(`/community/narrative/${nid}/react`, { emoji });
      setNarrative((list) => (list || []).map((t) => (t.id === nid ? res.data : t)));
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Reaction failed.");
    }
  };

  const sendReply = async () => {
    if (!replyBody.trim()) return;
    setReplying(true);
    try {
      await api.post(`/community/threads/${selected.thread.id}/replies`, { body: replyBody });
      setReplyBody("");
      await openThread(selected.thread.id);
      loadLounge();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Reply failed.");
    } finally {
      setReplying(false);
    }
  };

  const togglePin = async (tid) => {
    try {
      const res = await api.post(`/community/threads/${tid}/pin`);
      toast.success(res.data.pinned ? "Discussion pinned to the top." : "Discussion unpinned.");
      if (selected?.thread?.id === tid) {
        setSelected({ ...selected, thread: { ...selected.thread, pinned: res.data.pinned } });
      }
      loadLounge();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not update the pin.");
    }
  };

  const toggleLock = async (tid) => {
    try {
      const res = await api.post(`/community/threads/${tid}/lock`);
      toast.success(res.data.locked ? "Discussion locked, readable, but closed to new replies." : "Discussion unlocked.");
      if (selected?.thread?.id === tid) {
        setSelected({ ...selected, thread: { ...selected.thread, locked: res.data.locked } });
      }
      loadLounge();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not update the lock.");
    }
  };

  const confirmDelete = async () => {
    const { type, id } = deleteTarget;
    try {
      if (type === "announcement") await api.delete(`/community/announcements/${id}`);
      if (type === "thread") await api.delete(`/community/threads/${id}`);
      if (type === "reply") await api.delete(`/community/replies/${id}`);
      if (type === "take") await api.delete(`/community/narrative/${id}`);
      toast.success("Deleted.");
      setDeleteTarget(null);
      if (type === "thread") setSelected(null);
      else if (type === "reply" && selected) await openThread(selected.thread.id);
      loadLounge();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Delete failed.");
    }
  };

  if (loading) {
    return <div className="container-editorial py-16"><Skeleton className="h-96 rounded-2xl" /></div>;
  }

  // ------- gated states -------
  if (!user || locked) {
    return (
      <div className="container-editorial py-16 sm:py-24" data-testid="community-locked">
        <Seo title="The Lounge" path="/lounge" />
        <div className="max-w-xl mx-auto text-center">
          <img
            src={pillarMascot("lounge")}
            alt={PILLAR_MASCOT_ALTS.lounge}
            className="h-32 w-32 lg:h-40 lg:w-40 rounded-full object-cover mx-auto mb-6 shadow-lg"
            style={{ border: `3px solid ${withAlpha(pillarAccent("lounge"), 0.55)}` }}
            loading="lazy"
            data-testid="lounge-locked-mascot"
          />
          <span className="section-label">Members only</span>
          <h1 className="font-serif text-3xl sm:text-4xl font-semibold mt-3 mb-4">The Lounge</h1>
          <p className="text-muted-foreground leading-relaxed mb-8">
            A private space for Premium members, the editor's live Market Narrative feed,
            early access to upcoming editions before they publish, and discussions with
            fellow readers on desks around the world.
          </p>
          {user ? (
            <Button onClick={() => navigate("/pricing")} className="bg-accent text-accent-foreground hover:bg-accent/90 h-11 px-8" data-testid="community-upgrade-button">
              <Crown className="h-4 w-4 mr-2" /> Go Premium to enter
            </Button>
          ) : (
            <Button onClick={() => navigate("/auth?next=/lounge")} className="bg-accent text-accent-foreground hover:bg-accent/90 h-11 px-8" data-testid="community-signin-button">
              Sign in to continue
            </Button>
          )}
        </div>
      </div>
    );
  }

  // ------- thread detail view -------
  if (selected) {
    const t = selected.thread;
    const canDeleteThread = isAdmin || t.author?.id === user.id;
    return (
      <div className="container-editorial py-10 sm:py-14" data-testid="community-thread-detail">
        <Seo title={t.title} path="/lounge" />
        <div className="max-w-2xl mx-auto">
          <Button variant="ghost" onClick={() => setSelected(null)} className="mb-6 -ml-2" data-testid="community-back-button">
            <ArrowLeft className="h-4 w-4 mr-2" /> All discussions
          </Button>
          <Card className="rounded-xl">
            <CardContent className="p-6">
              <div className="flex items-start justify-between gap-3">
                <h1 className="font-serif text-2xl font-semibold leading-snug flex items-start gap-2">
                  {t.pinned && <Pin className="h-4 w-4 text-accent mt-1.5 shrink-0" data-testid="community-thread-pinned-icon" />}
                  {t.title}
                </h1>
                <div className="flex gap-1 shrink-0">
                  {isAdmin && (
                    <Button variant="ghost" size="icon" onClick={() => toggleLock(t.id)} data-testid="community-lock-thread-button" aria-label={t.locked ? "Unlock discussion" : "Lock discussion"}>
                      {t.locked ? <Lock className="h-4 w-4 text-accent" /> : <LockOpen className="h-4 w-4" />}
                    </Button>
                  )}
                  {isAdmin && (
                    <Button variant="ghost" size="icon" onClick={() => togglePin(t.id)} data-testid="community-pin-thread-button" aria-label={t.pinned ? "Unpin discussion" : "Pin discussion"}>
                      <Pin className={`h-4 w-4 ${t.pinned ? "text-accent" : ""}`} />
                    </Button>
                  )}
                  {canDeleteThread && (
                    <Button variant="ghost" size="icon" className="text-destructive" onClick={() => setDeleteTarget({ type: "thread", id: t.id })} data-testid="community-delete-thread-button" aria-label="Delete discussion">
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              </div>
              <div className="mt-3 mb-4"><AuthorLine author={t.author} date={t.created_at} onProfile={openProfile} /></div>
              <p className="text-sm leading-relaxed whitespace-pre-wrap">{t.body}</p>
            </CardContent>
          </Card>

          <h2 className="font-serif text-lg font-semibold mt-8 mb-4">
            {selected.replies.length} {selected.replies.length === 1 ? "reply" : "replies"}
          </h2>
          <div className="space-y-3" data-testid="community-replies-list">
            {selected.replies.map((r) => (
              <Card key={r.id} className="rounded-xl">
                <CardContent className="p-4">
                  <div className="flex items-start justify-between gap-3">
                    <AuthorLine author={r.author} date={r.created_at} onProfile={openProfile} />
                    {(isAdmin || r.author?.id === user.id) && (
                      <Button variant="ghost" size="icon" className="h-7 w-7 text-destructive shrink-0" onClick={() => setDeleteTarget({ type: "reply", id: r.id })} data-testid={`community-delete-reply-${r.id}`} aria-label="Delete reply">
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    )}
                  </div>
                  <p className="text-sm leading-relaxed whitespace-pre-wrap mt-2">{r.body}</p>
                </CardContent>
              </Card>
            ))}
            {selected.replies.length === 0 && (
              <p className="text-sm text-muted-foreground" data-testid="community-no-replies">No replies yet, be the first to weigh in.</p>
            )}
          </div>

          {t.locked ? (
            <Card className="rounded-xl mt-6 border-dashed">
              <CardContent className="p-4 flex items-center gap-3 text-sm text-muted-foreground" data-testid="community-locked-notice">
                <Lock className="h-4 w-4 text-accent shrink-0" />
                This discussion is locked, it stays readable, but new replies are closed.
              </CardContent>
            </Card>
          ) : (
            <div className="mt-6 flex gap-2">
              <Textarea
                value={replyBody}
                onChange={(e) => setReplyBody(e.target.value)}
                placeholder="Add your reply…"
                rows={2}
                className="resize-none"
                data-testid="community-reply-input"
              />
              <Button onClick={sendReply} disabled={replying || !replyBody.trim()} className="bg-accent text-accent-foreground hover:bg-accent/90 self-end" data-testid="community-reply-submit">
                <Send className="h-4 w-4" />
              </Button>
            </div>
          )}
        </div>

        <DeleteDialog target={deleteTarget} onCancel={() => setDeleteTarget(null)} onConfirm={confirmDelete} />
        <ProfileDialog open={profileOpen} onOpenChange={setProfileOpen} profile={profile} onOpenThread={(tid) => { setProfileOpen(false); openThread(tid); }} />
      </div>
    );
  }

  // ------- lounge home -------
  return (
    <div className="container-editorial py-10 sm:py-14" data-testid="community-page">
      <Seo title="The Lounge" path="/lounge" />
      <div
        className="relative overflow-hidden rounded-2xl border px-6 sm:px-10 py-8 sm:py-10 mb-8"
        style={{ borderColor: withAlpha(pillarAccent("lounge"), 0.35), backgroundColor: withAlpha(pillarAccent("lounge"), 0.07) }}
        data-testid="lounge-header-banner"
      >
        <div className="absolute inset-y-0 right-0 w-3/4 sm:w-1/2 pointer-events-none" style={{ color: pillarAccent("lounge"), opacity: 0.16 }}>
          <PillarMotif category="lounge" className="h-full w-full" />
        </div>
        <div className="relative flex items-center gap-6 sm:gap-10">
          <div className="min-w-0 flex-1">
            <span className="font-mono text-[11px] uppercase tracking-[0.18em]" style={{ color: pillarAccent("lounge") }}>
              Members only · The Signal Wolf
            </span>
            <h1 className="font-serif text-3xl sm:text-4xl font-semibold mt-3 flex items-center gap-3">
              The Lounge <Crown className="h-6 w-6 text-accent" />
            </h1>
            <p className="text-sm text-muted-foreground mt-3 max-w-2xl leading-relaxed">Live market takes, early-access drafts, announcements, and discussions between Premium readers.</p>
            <div className="h-1 w-16 rounded-full mt-4" style={{ backgroundColor: pillarAccent("lounge") }} aria-hidden />
            <div className="flex flex-wrap gap-2 mt-5">
              {isAdmin && (
                <Button variant="outline" onClick={() => openAnnEditor()} data-testid="community-new-announcement-button">
                  <Megaphone className="h-4 w-4 mr-2" /> New announcement
                </Button>
              )}
              <Button onClick={() => setNewThreadOpen(true)} className="bg-accent text-accent-foreground hover:bg-accent/90" data-testid="community-new-thread-button">
                <Plus className="h-4 w-4 mr-2" /> Start a discussion
              </Button>
            </div>
          </div>
          <img
            src={pillarMascot("lounge")}
            alt={PILLAR_MASCOT_ALTS.lounge}
            className="hidden sm:block h-32 w-32 lg:h-40 lg:w-40 rounded-full object-cover shrink-0 shadow-lg"
            style={{ border: `3px solid ${withAlpha(pillarAccent("lounge"), 0.55)}` }}
            loading="lazy"
            data-testid="lounge-mascot"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Announcements */}
        <div className="lg:col-span-1">
          <h2 className="font-serif text-xl font-semibold mb-4 flex items-center gap-2">
            <Megaphone className="h-4 w-4 text-accent" /> Announcements
          </h2>
          {announcements === null ? (
            <Skeleton className="h-40 rounded-xl" />
          ) : announcements.length === 0 ? (
            <Card className="rounded-xl">
              <CardContent className="p-6 text-sm text-muted-foreground" data-testid="community-no-announcements">
                Nothing from the desk yet. Announcements land here first.
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-3" data-testid="community-announcements-list">
              {announcements.map((a) => (
                <Card key={a.id} className="rounded-xl border-accent/20">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between gap-2">
                      <h3 className="font-medium text-sm flex items-center gap-2">
                        {a.title}
                        {a.scheduled && (
                          <Badge variant="secondary" className="gap-1 text-[9px] px-1.5 py-0" data-testid={`community-scheduled-badge-${a.id}`}>
                            <CalendarClock className="h-3 w-3" /> Scheduled
                          </Badge>
                        )}
                      </h3>
                      {isAdmin && (
                        <div className="flex gap-0.5 shrink-0">
                          <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => openAnnEditor(a)} data-testid={`community-edit-announcement-${a.id}`} aria-label="Edit announcement">
                            <Pencil className="h-3.5 w-3.5" />
                          </Button>
                          <Button variant="ghost" size="icon" className="h-6 w-6 text-destructive" onClick={() => setDeleteTarget({ type: "announcement", id: a.id })} data-testid={`community-delete-announcement-${a.id}`} aria-label="Delete announcement">
                            <Trash2 className="h-3.5 w-3.5" />
                          </Button>
                        </div>
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground leading-relaxed mt-1.5 whitespace-pre-wrap">{a.body}</p>
                    <p className="text-[10px] font-mono text-muted-foreground mt-2">
                      {a.scheduled ? `publishes ${formatDate(a.publish_at)}` : formatDate(a.created_at)}
                    </p>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>

        {/* Main hub: Discussions | Market Narrative | Early access */}
        <div className="lg:col-span-2">
          <Tabs defaultValue="narrative" data-testid="lounge-tabs">
            <TabsList className="mb-4">
              <TabsTrigger value="narrative" data-testid="lounge-tab-narrative">
                <Activity className="h-3.5 w-3.5 mr-1.5" /> Market Narrative
              </TabsTrigger>
              <TabsTrigger value="discussions" data-testid="lounge-tab-discussions">
                <MessagesSquare className="h-3.5 w-3.5 mr-1.5" /> Discussions
              </TabsTrigger>
              <TabsTrigger value="early" data-testid="lounge-tab-early">
                <CalendarClock className="h-3.5 w-3.5 mr-1.5" /> Early access
              </TabsTrigger>
            </TabsList>

            {/* ---- Market Narrative: the editor's live raw takes ---- */}
            <TabsContent value="narrative">
              <p className="text-sm text-muted-foreground mb-4">
                Quick, raw takes from the desk, the market notes that don't make the weekly briefing.
              </p>
              {isAdmin && (
                <Card className="rounded-xl mb-4 border-accent/30" data-testid="narrative-composer">
                  <CardContent className="p-4 space-y-3">
                    <Textarea
                      value={takeForm.body}
                      onChange={(e) => setTakeForm({ ...takeForm, body: e.target.value })}
                      placeholder="Drop a quick take, what's moving and why it matters…"
                      rows={2}
                      className="resize-none"
                      data-testid="narrative-composer-input"
                    />
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="flex gap-1.5">
                        {NARRATIVE_TAGS.map(({ value, label, Icon }) => (
                          <button
                            key={value}
                            type="button"
                            onClick={() => setTakeForm({ ...takeForm, tag: takeForm.tag === value ? "" : value })}
                            className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-xs transition-colors ${
                              takeForm.tag === value
                                ? "border-accent/50 bg-accent/10 text-accent"
                                : "border-border text-muted-foreground hover:border-accent/40"
                            }`}
                            data-testid={`narrative-tag-${value}`}
                          >
                            <Icon className="h-3 w-3" /> {label}
                          </button>
                        ))}
                      </div>
                      <Button size="sm" onClick={postTake} disabled={takeBusy || !takeForm.body.trim()} className="bg-accent text-accent-foreground hover:bg-accent/90" data-testid="narrative-composer-submit">
                        {takeBusy ? "Posting…" : "Post take"}
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              )}
              {narrative === null ? (
                <Skeleton className="h-40 rounded-xl" />
              ) : narrative.length === 0 ? (
                <Card className="rounded-xl">
                  <CardContent className="py-12 text-center" data-testid="narrative-empty">
                    <Activity className="h-9 w-9 text-muted-foreground mx-auto mb-3" />
                    <h3 className="font-serif text-lg font-semibold mb-1">No takes yet</h3>
                    <p className="text-sm text-muted-foreground">When markets move, the editor's raw notes land here first.</p>
                  </CardContent>
                </Card>
              ) : (
                <div className="space-y-3" data-testid="narrative-feed">
                  {narrative.map((t) => {
                    const tagMeta = NARRATIVE_TAGS.find((x) => x.value === t.tag);
                    return (
                      <Card key={t.id} className="rounded-xl" data-testid={`narrative-take-${t.id}`}>
                        <CardContent className="p-4">
                          <div className="flex items-start justify-between gap-3">
                            <div className="flex items-center gap-2 flex-wrap">
                              <AuthorLine author={t.author} date={t.created_at} onProfile={openProfile} />
                              {tagMeta && (
                                <Badge variant="secondary" className="gap-1 text-[10px] px-1.5 py-0" data-testid={`narrative-take-tag-${t.id}`}>
                                  <tagMeta.Icon className="h-3 w-3" /> {tagMeta.label}
                                </Badge>
                              )}
                            </div>
                            {isAdmin && (
                              <Button variant="ghost" size="icon" className="h-6 w-6 text-destructive shrink-0" onClick={() => setDeleteTarget({ type: "take", id: t.id })} data-testid={`narrative-delete-${t.id}`} aria-label="Delete take">
                                <Trash2 className="h-3.5 w-3.5" />
                              </Button>
                            )}
                          </div>
                          <p className="text-sm leading-relaxed whitespace-pre-wrap mt-2">{t.body}</p>
                          <div className="flex gap-1.5 mt-3">
                            {REACTIONS.map((emoji) => (
                              <button
                                key={emoji}
                                type="button"
                                onClick={() => reactToTake(t.id, emoji)}
                                className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs transition-colors ${
                                  t.my_reaction === emoji
                                    ? "border-accent/50 bg-accent/10"
                                    : "border-border hover:border-accent/40"
                                }`}
                                data-testid={`narrative-react-${t.id}-${emoji}`}
                                aria-label={`React ${emoji}`}
                              >
                                <span>{emoji}</span>
                                {t.reactions?.[emoji] > 0 && <span className="font-mono tabular-nums">{t.reactions[emoji]}</span>}
                              </button>
                            ))}
                          </div>
                        </CardContent>
                      </Card>
                    );
                  })}
                </div>
              )}
            </TabsContent>

            {/* ---- Discussions ---- */}
            <TabsContent value="discussions">
              {threads === null ? (
                <Skeleton className="h-64 rounded-xl" />
              ) : threads.length === 0 ? (
                <Card className="rounded-xl">
                  <CardContent className="py-14 text-center" data-testid="community-no-threads">
                    <MessagesSquare className="h-9 w-9 text-muted-foreground mx-auto mb-3" />
                    <h3 className="font-serif text-lg font-semibold mb-1">No discussions yet</h3>
                    <p className="text-sm text-muted-foreground mb-5">Kick things off, what's on your mind this week?</p>
                    <Button onClick={() => setNewThreadOpen(true)} variant="outline" data-testid="community-empty-start-button">
                      <Plus className="h-4 w-4 mr-2" /> Start the first discussion
                    </Button>
                  </CardContent>
                </Card>
              ) : (
                <div className="space-y-3" data-testid="community-threads-list">
                  {threads.map((t) => (
                    <button
                      key={t.id}
                      onClick={() => openThread(t.id)}
                      disabled={detailBusy}
                      className="w-full text-left"
                      data-testid={`community-thread-${t.id}`}
                    >
                      <Card className={`rounded-xl transition-colors duration-150 hover:border-accent/40 ${t.pinned ? "border-accent/30 bg-accent/[0.03]" : ""}`}>
                        <CardContent className="p-4">
                          <div className="flex items-center gap-2">
                            {t.pinned && (
                              <Badge className="bg-accent/10 text-accent border-accent/30 hover:bg-accent/10 gap-1 text-[10px] px-1.5 py-0" data-testid={`community-pinned-badge-${t.id}`}>
                                <Pin className="h-3 w-3" /> Pinned
                              </Badge>
                            )}
                            {t.locked && (
                              <Badge variant="secondary" className="gap-1 text-[10px] px-1.5 py-0" data-testid={`community-locked-badge-${t.id}`}>
                                <Lock className="h-3 w-3" /> Locked
                              </Badge>
                            )}
                            <h3 className="font-medium">{t.title}</h3>
                          </div>
                          <p className="text-sm text-muted-foreground line-clamp-2 mt-1">{t.body}</p>
                          <div className="flex items-center justify-between mt-3">
                            <AuthorLine author={t.author} date={t.created_at} onProfile={openProfile} />
                            <span className="text-xs font-mono text-muted-foreground flex items-center gap-1">
                              <MessagesSquare className="h-3.5 w-3.5" /> {t.reply_count}
                            </span>
                          </div>
                        </CardContent>
                      </Card>
                    </button>
                  ))}
                </div>
              )}
            </TabsContent>

            {/* ---- Early access: read scheduled drafts before everyone ---- */}
            <TabsContent value="early">
              <p className="text-sm text-muted-foreground mb-4">
                Scheduled essays and briefings, readable here before they publish for everyone.
              </p>
              {drafts === null ? (
                <Skeleton className="h-40 rounded-xl" />
              ) : drafts.length === 0 ? (
                <Card className="rounded-xl">
                  <CardContent className="py-12 text-center" data-testid="early-access-empty">
                    <CalendarClock className="h-9 w-9 text-muted-foreground mx-auto mb-3" />
                    <h3 className="font-serif text-lg font-semibold mb-1">Nothing scheduled right now</h3>
                    <p className="text-sm text-muted-foreground">When the next edition is drafted, you'll read it here first.</p>
                  </CardContent>
                </Card>
              ) : (
                <div className="space-y-3" data-testid="early-access-list">
                  {drafts.map((d) => (
                    <button
                      key={d.id}
                      onClick={() => navigate(`/post/${d.slug}`)}
                      className="w-full text-left"
                      data-testid={`early-access-draft-${d.id}`}
                    >
                      <Card className="rounded-xl border-accent/30 transition-colors duration-150 hover:border-accent/60">
                        <CardContent className="p-4">
                          <div className="flex items-center gap-2 flex-wrap">
                            <Badge className="bg-accent/10 text-accent border-accent/30 hover:bg-accent/10 gap-1 text-[10px] px-1.5 py-0">
                              <CalendarClock className="h-3 w-3" /> Early access
                            </Badge>
                            {d.edition && <Badge variant="secondary" className="text-[10px] px-1.5 py-0">Edition #{d.edition}</Badge>}
                          </div>
                          <h3 className="font-serif text-lg font-semibold mt-2">{d.title}</h3>
                          <p className="text-sm text-muted-foreground line-clamp-2 mt-1">{d.excerpt}</p>
                          <div className="flex items-center justify-between mt-3">
                            <span className="text-[11px] font-mono text-muted-foreground">publishes {formatDate(d.publish_at)}</span>
                            <span className="text-xs text-accent flex items-center gap-1 font-medium">
                              Read it now <ArrowRight className="h-3.5 w-3.5" />
                            </span>
                          </div>
                        </CardContent>
                      </Card>
                    </button>
                  ))}
                </div>
              )}
            </TabsContent>
          </Tabs>
        </div>
      </div>

      {/* New discussion dialog */}
      <Dialog open={newThreadOpen} onOpenChange={setNewThreadOpen}>
        <DialogContent data-testid="community-new-thread-dialog">
          <DialogHeader>
            <DialogTitle className="font-serif text-2xl">Start a discussion</DialogTitle>
            <DialogDescription>Visible to all Premium members in the Lounge.</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="thread-title">Title</Label>
              <Input id="thread-title" value={threadForm.title} onChange={(e) => setThreadForm({ ...threadForm, title: e.target.value })} placeholder="What do you want to talk about?" data-testid="community-thread-title-input" />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="thread-body">Your post</Label>
              <Textarea id="thread-body" rows={4} value={threadForm.body} onChange={(e) => setThreadForm({ ...threadForm, body: e.target.value })} placeholder="Share your take, question, or find…" data-testid="community-thread-body-input" />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setNewThreadOpen(false)}>Cancel</Button>
            <Button onClick={createThread} disabled={posting} className="bg-accent text-accent-foreground hover:bg-accent/90" data-testid="community-thread-submit">
              {posting ? "Posting…" : "Post discussion"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* New announcement dialog (admin) */}
      <Dialog open={annOpen} onOpenChange={(o) => { setAnnOpen(o); if (!o) setAnnEditing(null); }}>
        <DialogContent data-testid="community-announcement-dialog">
          <DialogHeader>
            <DialogTitle className="font-serif text-2xl">{annEditing ? "Edit announcement" : "Post an announcement"}</DialogTitle>
            <DialogDescription>{annEditing ? "Changes apply immediately, clear the schedule to publish now." : "Pinned to the Lounge for all Premium members."}</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="ann-title">Title</Label>
              <Input id="ann-title" value={annForm.title} onChange={(e) => setAnnForm({ ...annForm, title: e.target.value })} data-testid="community-announcement-title-input" />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="ann-body">Announcement</Label>
              <Textarea id="ann-body" rows={4} value={annForm.body} onChange={(e) => setAnnForm({ ...annForm, body: e.target.value })} data-testid="community-announcement-body-input" />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="ann-publish">Schedule for later <span className="text-muted-foreground font-normal">(optional, leave empty to publish now)</span></Label>
              <Input
                id="ann-publish"
                type="datetime-local"
                value={annForm.publish_at}
                onChange={(e) => setAnnForm({ ...annForm, publish_at: e.target.value })}
                data-testid="community-announcement-schedule-input"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setAnnOpen(false)}>Cancel</Button>
            <Button onClick={createAnnouncement} disabled={annBusy} className="bg-accent text-accent-foreground hover:bg-accent/90" data-testid="community-announcement-submit">
              {annBusy ? "Saving…" : annEditing ? (annForm.publish_at ? "Save & reschedule" : "Save changes") : annForm.publish_at ? "Schedule announcement" : "Post announcement"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <DeleteDialog target={deleteTarget} onCancel={() => setDeleteTarget(null)} onConfirm={confirmDelete} />
      <ProfileDialog open={profileOpen} onOpenChange={setProfileOpen} profile={profile} onOpenThread={(tid) => { setProfileOpen(false); openThread(tid); }} />
    </div>
  );
}

const ProfileDialog = ({ open, onOpenChange, profile, onOpenThread }) => (
  <Dialog open={open} onOpenChange={onOpenChange}>
    <DialogContent className="max-w-md" data-testid="community-profile-dialog">
      {profile === null ? (
        <div className="space-y-3 py-4">
          <Skeleton className="h-14 w-14 rounded-full" />
          <Skeleton className="h-5 w-40" />
          <Skeleton className="h-20 w-full" />
        </div>
      ) : (
        <>
          <DialogHeader>
            <div className="flex items-center gap-4">
              <Avatar className="h-14 w-14 border border-border">
                <AvatarFallback className="bg-secondary text-lg font-medium">{initials(profile.name)}</AvatarFallback>
              </Avatar>
              <div>
                <DialogTitle className="font-serif text-2xl flex items-center gap-2" data-testid="community-profile-name">
                  {profile.name}
                  {profile.role === "admin" && (
                    <Badge className="bg-accent/10 text-accent border-accent/30 hover:bg-accent/10 text-[10px]">Editor</Badge>
                  )}
                  {profile.is_premium && profile.role !== "admin" && (
                    <Badge className="bg-accent/10 text-accent border-accent/30 hover:bg-accent/10 gap-1 text-[10px]"><Crown className="h-3 w-3" /> Premium</Badge>
                  )}
                </DialogTitle>
                <DialogDescription data-testid="community-profile-joined">
                  Member since {formatDate(profile.joined)}
                </DialogDescription>
              </div>
            </div>
          </DialogHeader>
          <div className="grid grid-cols-2 gap-3">
            <div className="rounded-lg border border-border p-3 text-center">
              <div className="text-xl font-semibold" data-testid="community-profile-thread-count">{profile.thread_count}</div>
              <div className="text-[10px] font-mono uppercase tracking-wider text-muted-foreground">Discussions</div>
            </div>
            <div className="rounded-lg border border-border p-3 text-center">
              <div className="text-xl font-semibold" data-testid="community-profile-reply-count">{profile.reply_count}</div>
              <div className="text-[10px] font-mono uppercase tracking-wider text-muted-foreground">Replies</div>
            </div>
          </div>
          {profile.recent_threads.length > 0 && (
            <div>
              <h4 className="text-xs font-mono uppercase tracking-wider text-muted-foreground mb-2">Recent discussions</h4>
              <div className="space-y-1.5" data-testid="community-profile-recent-threads">
                {profile.recent_threads.map((t) => (
                  <button
                    key={t.id}
                    onClick={() => onOpenThread(t.id)}
                    className="w-full text-left text-sm rounded-lg border border-border px-3 py-2 hover:border-accent/40 transition-colors flex items-center justify-between gap-2"
                  >
                    <span className="line-clamp-1">{t.title}</span>
                    <span className="text-xs font-mono text-muted-foreground flex items-center gap-1 shrink-0">
                      <MessagesSquare className="h-3 w-3" /> {t.reply_count}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </DialogContent>
  </Dialog>
);

const DeleteDialog = ({ target, onCancel, onConfirm }) => (
  <AlertDialog open={!!target} onOpenChange={(o) => !o && onCancel()}>
    <AlertDialogContent data-testid="community-delete-dialog">
      <AlertDialogHeader>
        <AlertDialogTitle className="font-serif">Delete this {target?.type}?</AlertDialogTitle>
        <AlertDialogDescription>This cannot be undone.</AlertDialogDescription>
      </AlertDialogHeader>
      <AlertDialogFooter>
        <AlertDialogCancel data-testid="community-delete-cancel">Keep it</AlertDialogCancel>
        <AlertDialogAction onClick={onConfirm} className="bg-destructive text-destructive-foreground hover:bg-destructive/90" data-testid="community-delete-confirm">
          Delete
        </AlertDialogAction>
      </AlertDialogFooter>
    </AlertDialogContent>
  </AlertDialog>
);
