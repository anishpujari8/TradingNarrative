import { useEffect, useState, useCallback } from "react";
import { useNavigate, Link } from "react-router-dom";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from "@/components/ui/dialog";
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { BarChart, Bar, XAxis, YAxis, Tooltip as ReTooltip, ResponsiveContainer } from "recharts";
import { Eye, Users, Crown, Mail, PenSquare, Trash2, Send, Plus, Newspaper } from "lucide-react";
import { toast } from "sonner";
import { Seo } from "@/components/Seo";
import { api, formatDate } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

const StatCard = ({ icon: Icon, label, value, testId }) => (
  <Card className="rounded-xl" data-testid={testId}>
    <CardContent className="p-5 flex items-center gap-4">
      <div className="w-10 h-10 rounded-lg bg-accent/10 flex items-center justify-center shrink-0">
        <Icon className="h-5 w-5 text-accent" />
      </div>
      <div>
        <div className="text-2xl font-semibold">{value ?? "—"}</div>
        <div className="text-xs text-muted-foreground font-mono uppercase tracking-wider">{label}</div>
      </div>
    </CardContent>
  </Card>
);

export default function AdminPage() {
  const { user, loading } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [posts, setPosts] = useState(null);
  const [subscribers, setSubscribers] = useState(null);
  const [issues, setIssues] = useState(null);
  const [emailLogs, setEmailLogs] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [issueDialog, setIssueDialog] = useState(false);
  const [digest, setDigest] = useState(null);
  const [digestOpen, setDigestOpen] = useState(false);
  const [digestBusy, setDigestBusy] = useState(false);
  const [digestSending, setDigestSending] = useState(false);
  const [issuePostId, setIssuePostId] = useState("");
  const [issueSubject, setIssueSubject] = useState("");
  const [sending, setSending] = useState(false);

  const loadAll = useCallback(() => {
    api.get("/admin/analytics/stats").then((r) => setStats(r.data)).catch(() => {});
    api.get("/admin/posts").then((r) => setPosts(r.data.posts)).catch(() => setPosts([]));
    api.get("/admin/newsletter/subscribers").then((r) => setSubscribers(r.data)).catch(() => {});
    api.get("/admin/newsletter/issues").then((r) => setIssues(r.data.issues)).catch(() => setIssues([]));
    api.get("/admin/email-logs").then((r) => setEmailLogs(r.data.logs)).catch(() => setEmailLogs([]));
  }, []);

  useEffect(() => {
    if (loading) return;
    if (!user) { navigate("/auth?next=/admin"); return; }
    if (user.role !== "admin") { navigate("/"); toast.error("Admin access required."); return; }
    loadAll();
  }, [user, loading, navigate, loadAll]);

  const deletePost = async () => {
    try {
      await api.delete(`/admin/posts/${deleteTarget.id}`);
      toast.success("Post deleted.");
      setDeleteTarget(null);
      loadAll();
    } catch {
      toast.error("Delete failed.");
    }
  };

  const openDigest = async () => {
    setDigestBusy(true);
    try {
      const res = await api.get("/admin/newsletter/digest-preview");
      setDigest(res.data);
      setDigestOpen(true);
    } catch {
      toast.error("Could not build the digest preview.");
    } finally {
      setDigestBusy(false);
    }
  };

  const sendDigest = async () => {
    setDigestSending(true);
    try {
      const res = await api.post("/admin/newsletter/send-digest", { subject: digest?.subject });
      toast.success(`Digest sent (mocked) to ${res.data.recipients} subscribers.`);
      setDigestOpen(false);
      loadAll();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Digest send failed.");
    } finally {
      setDigestSending(false);
    }
  };

  const sendIssue = async () => {
    if (!issuePostId) { toast.error("Pick a post to send."); return; }
    setSending(true);
    try {
      const res = await api.post("/admin/newsletter/issues", { post_id: issuePostId, subject: issueSubject || undefined });
      toast.success(`Issue sent (mocked) to ${res.data.recipients} subscribers.`);
      setIssueDialog(false);
      setIssuePostId("");
      setIssueSubject("");
      loadAll();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Send failed.");
    } finally {
      setSending(false);
    }
  };

  if (loading || !user || user.role !== "admin") {
    return <div className="container-editorial py-16"><Skeleton className="h-96 rounded-2xl" /></div>;
  }

  const statusBadge = (p) => {
    if (p.status === "published") return <Badge className="bg-accent/10 text-accent border-accent/30 hover:bg-accent/10">Published</Badge>;
    if (p.status === "scheduled") return <Badge variant="secondary">Scheduled</Badge>;
    return <Badge variant="outline">Draft</Badge>;
  };

  return (
    <div className="container-editorial py-10 sm:py-14" data-testid="admin-page">
      <Seo title="Admin Studio" path="/admin" />
      <div className="flex flex-wrap items-center justify-between gap-4 mb-8">
        <div>
          <span className="section-label">Admin Studio</span>
          <h1 className="font-serif text-3xl sm:text-4xl font-semibold mt-2">Run the publication</h1>
        </div>
        <Button onClick={() => navigate("/admin/editor")} className="bg-accent text-accent-foreground hover:bg-accent/90" data-testid="admin-new-post-button">
          <Plus className="h-4 w-4 mr-2" /> New post
        </Button>
      </div>

      <Tabs defaultValue="overview">
        <TabsList className="flex flex-wrap h-auto justify-start mb-6">
          <TabsTrigger value="overview" data-testid="admin-tab-overview">Overview</TabsTrigger>
          <TabsTrigger value="posts" data-testid="admin-tab-posts">Posts</TabsTrigger>
          <TabsTrigger value="newsletter" data-testid="admin-tab-newsletter">Newsletter</TabsTrigger>
          <TabsTrigger value="emails" data-testid="admin-tab-emails">Email log</TabsTrigger>
        </TabsList>

        {/* OVERVIEW */}
        <TabsContent value="overview">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <StatCard icon={Eye} label="Pageviews" value={stats?.pageviews} testId="admin-stat-pageviews" />
            <StatCard icon={Mail} label="Newsletter subs" value={stats?.newsletter_subscribers} testId="admin-stat-subscribers" />
            <StatCard icon={Users} label="Accounts" value={stats?.users} testId="admin-stat-users" />
            <StatCard icon={Crown} label="Premium members" value={stats?.premium_subscribers} testId="admin-stat-premium" />
          </div>
          <Card className="rounded-xl">
            <CardHeader><CardTitle className="font-serif text-xl">Top posts by views</CardTitle></CardHeader>
            <CardContent className="h-72" data-testid="admin-analytics-top-posts-chart">
              {stats?.top_posts?.length ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={stats.top_posts} layout="vertical" margin={{ left: 10, right: 20 }}>
                    <XAxis type="number" hide />
                    <YAxis type="category" dataKey="title" width={220} tick={{ fontSize: 11 }} />
                    <ReTooltip cursor={{ fill: "hsla(168,52%,34%,0.06)" }} />
                    <Bar dataKey="views" fill="hsl(168 52% 34%)" radius={[0, 6, 6, 0]} barSize={18} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <Skeleton className="h-full" />
              )}
            </CardContent>
          </Card>
          <div className="grid grid-cols-2 gap-4 mt-4">
            <StatCard icon={Eye} label="Pageviews (7d)" value={stats?.pageviews_7d} testId="admin-stat-pageviews-7d" />
            <StatCard icon={Crown} label="Checkouts completed" value={stats?.checkouts} testId="admin-stat-checkouts" />
          </div>
        </TabsContent>

        {/* POSTS */}
        <TabsContent value="posts">
          <Card className="rounded-xl">
            <CardContent className="p-0">
              {posts === null ? (
                <div className="p-6"><Skeleton className="h-64" /></div>
              ) : (
                <Table data-testid="admin-posts-table">
                  <TableHeader>
                    <TableRow>
                      <TableHead>Title</TableHead>
                      <TableHead>Category</TableHead>
                      <TableHead>Tier</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Published</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {posts.map((p) => (
                      <TableRow key={p.id} data-testid={`admin-post-row-${p.slug}`}>
                        <TableCell className="max-w-xs">
                          <Link to={`/post/${p.slug}`} className="font-medium hover:text-accent transition-colors line-clamp-1">{p.title}</Link>
                        </TableCell>
                        <TableCell><Badge variant="secondary" className="font-mono text-[10px] uppercase">{p.category_label}</Badge></TableCell>
                        <TableCell>
                          {p.tier === "premium"
                            ? <Badge className="bg-accent/10 text-accent border-accent/30 hover:bg-accent/10">Premium</Badge>
                            : <Badge variant="outline">Free</Badge>}
                        </TableCell>
                        <TableCell>{statusBadge(p)}</TableCell>
                        <TableCell className="text-xs font-mono text-muted-foreground">{formatDate(p.published_at)}</TableCell>
                        <TableCell className="text-right">
                          <div className="flex justify-end gap-1">
                            <Button variant="ghost" size="icon" onClick={() => navigate(`/admin/editor/${p.id}`)} data-testid={`admin-edit-${p.slug}`} aria-label="Edit">
                              <PenSquare className="h-4 w-4" />
                            </Button>
                            <Button variant="ghost" size="icon" className="text-destructive" onClick={() => setDeleteTarget(p)} data-testid={`admin-delete-${p.slug}`} aria-label="Delete">
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* NEWSLETTER */}
        <TabsContent value="newsletter">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="rounded-xl">
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle className="font-serif text-xl">Subscribers ({subscribers?.total ?? "…"})</CardTitle>
                <div className="flex gap-2">
                  <Button variant="outline" onClick={openDigest} disabled={digestBusy} data-testid="admin-digest-preview-button">
                    <Newspaper className="h-4 w-4 mr-2" /> {digestBusy ? "Building…" : "Weekly digest"}
                  </Button>
                  <Button onClick={() => setIssueDialog(true)} className="bg-accent text-accent-foreground hover:bg-accent/90" data-testid="admin-send-issue-button">
                    <Send className="h-4 w-4 mr-2" /> Send issue
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                {subscribers?.subscribers?.length ? (
                  <div className="max-h-80 overflow-y-auto">
                    <Table data-testid="admin-subscribers-table">
                      <TableHeader>
                        <TableRow><TableHead>Email</TableHead><TableHead>Source</TableHead><TableHead>Joined</TableHead></TableRow>
                      </TableHeader>
                      <TableBody>
                        {subscribers.subscribers.map((s) => (
                          <TableRow key={s.id}>
                            <TableCell className="text-sm">{s.email}</TableCell>
                            <TableCell className="text-xs font-mono text-muted-foreground">{s.source}</TableCell>
                            <TableCell className="text-xs font-mono text-muted-foreground">{formatDate(s.created_at)}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground" data-testid="admin-no-subscribers">No subscribers yet.</p>
                )}
              </CardContent>
            </Card>
            <Card className="rounded-xl">
              <CardHeader><CardTitle className="font-serif text-xl">Sent issues</CardTitle></CardHeader>
              <CardContent>
                {issues?.length ? (
                  <div className="space-y-3" data-testid="admin-issues-list">
                    {issues.map((i) => (
                      <div key={i.id} className="border border-border rounded-lg p-3">
                        <div className="font-medium text-sm">{i.subject}</div>
                        <div className="text-xs text-muted-foreground font-mono mt-1">
                          {formatDate(i.sent_at)} · {i.recipients} recipients · {i.status}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground" data-testid="admin-no-issues">No issues sent yet. Newsletter sends are MOCKED — swap in a real provider anytime.</p>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* EMAIL LOG */}
        <TabsContent value="emails">
          <Card className="rounded-xl">
            <CardHeader>
              <CardTitle className="font-serif text-xl">Email log (mocked provider)</CardTitle>
            </CardHeader>
            <CardContent>
              {emailLogs === null ? (
                <Skeleton className="h-40" />
              ) : emailLogs.length === 0 ? (
                <p className="text-sm text-muted-foreground">No emails logged yet.</p>
              ) : (
                <Table data-testid="admin-email-logs-table">
                  <TableHeader>
                    <TableRow><TableHead>To</TableHead><TableHead>Subject</TableHead><TableHead>Kind</TableHead><TableHead>Sent</TableHead></TableRow>
                  </TableHeader>
                  <TableBody>
                    {emailLogs.map((l) => (
                      <TableRow key={l.id}>
                        <TableCell className="text-sm">{l.to}</TableCell>
                        <TableCell className="text-sm max-w-xs truncate">{l.subject}</TableCell>
                        <TableCell><Badge variant="secondary" className="font-mono text-[10px]">{l.kind}</Badge></TableCell>
                        <TableCell className="text-xs font-mono text-muted-foreground">{formatDate(l.sent_at)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Delete confirm */}
      <AlertDialog open={!!deleteTarget} onOpenChange={(o) => !o && setDeleteTarget(null)}>
        <AlertDialogContent data-testid="admin-delete-dialog">
          <AlertDialogHeader>
            <AlertDialogTitle className="font-serif">Delete "{deleteTarget?.title}"?</AlertDialogTitle>
            <AlertDialogDescription>This permanently removes the post. This action cannot be undone.</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel data-testid="admin-delete-cancel">Keep it</AlertDialogCancel>
            <AlertDialogAction onClick={deletePost} className="bg-destructive text-destructive-foreground hover:bg-destructive/90" data-testid="admin-delete-confirm">
              Delete post
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Weekly digest preview dialog */}
      <Dialog open={digestOpen} onOpenChange={setDigestOpen}>
        <DialogContent className="max-w-2xl" data-testid="admin-digest-dialog">
          <DialogHeader>
            <DialogTitle className="font-serif text-2xl">Weekly digest preview</DialogTitle>
            <DialogDescription>
              {digest ? `${digest.post_count} essays from the past week · Subject: "${digest.subject}"` : ""} Sending is MOCKED and logged in the email log.
            </DialogDescription>
          </DialogHeader>
          {digest && (
            <div className="border border-border rounded-lg overflow-hidden bg-white">
              <iframe
                title="Digest preview"
                srcDoc={digest.html}
                className="w-full h-[420px]"
                sandbox=""
                data-testid="admin-digest-iframe"
              />
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setDigestOpen(false)}>Close</Button>
            <Button onClick={sendDigest} disabled={digestSending} className="bg-accent text-accent-foreground hover:bg-accent/90" data-testid="admin-digest-send-button">
              <Send className="h-4 w-4 mr-2" /> {digestSending ? "Sending…" : "Send to all subscribers"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Send issue dialog */}
      <Dialog open={issueDialog} onOpenChange={setIssueDialog}>
        <DialogContent data-testid="admin-issue-dialog">
          <DialogHeader>
            <DialogTitle className="font-serif text-2xl">Send a newsletter issue</DialogTitle>
            <DialogDescription>
              Turns a post into a newsletter issue for all subscribers. Sending is MOCKED — every send is logged in the email log.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-1.5">
              <Label>Post</Label>
              <Select value={issuePostId} onValueChange={setIssuePostId}>
                <SelectTrigger data-testid="admin-issue-post-select"><SelectValue placeholder="Choose a post…" /></SelectTrigger>
                <SelectContent>
                  {(posts || []).filter((p) => p.status === "published").map((p) => (
                    <SelectItem key={p.id} value={p.id}>{p.title}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label>Subject (optional)</Label>
              <Input value={issueSubject} onChange={(e) => setIssueSubject(e.target.value)} placeholder="Defaults to the post title" data-testid="admin-issue-subject-input" />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIssueDialog(false)}>Cancel</Button>
            <Button onClick={sendIssue} disabled={sending} className="bg-accent text-accent-foreground hover:bg-accent/90" data-testid="admin-issue-send-confirm">
              <Send className="h-4 w-4 mr-2" /> {sending ? "Sending…" : "Send to all subscribers"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
