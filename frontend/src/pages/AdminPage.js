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
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, Tooltip as ReTooltip, Legend, ResponsiveContainer } from "recharts";
import { Eye, Users, Crown, Mail, PenSquare, Trash2, Send, Plus, Newspaper, Globe, TrendingUp } from "lucide-react";
import { toast } from "sonner";
import { Seo } from "@/components/Seo";
import { api, formatDate } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

const TREND_COLORS = [
  "hsl(168 52% 34%)",
  "hsl(30 65% 50%)",
  "hsl(210 55% 48%)",
  "hsl(280 35% 52%)",
  "hsl(0 50% 52%)",
  "hsl(45 60% 42%)",
];

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
  const [traffic, setTraffic] = useState(null);
  const [trafficDays, setTrafficDays] = useState("30");

  const loadAll = useCallback(() => {
    api.get("/admin/analytics/stats").then((r) => setStats(r.data)).catch(() => {});
    api.get("/admin/posts").then((r) => setPosts(r.data.posts)).catch(() => setPosts([]));
    api.get("/admin/newsletter/subscribers").then((r) => setSubscribers(r.data)).catch(() => {});
    api.get("/admin/newsletter/issues").then((r) => setIssues(r.data.issues)).catch(() => setIssues([]));
    api.get("/admin/email-logs").then((r) => setEmailLogs(r.data.logs)).catch(() => setEmailLogs([]));
  }, []);

  useEffect(() => {
    if (!user || user.role !== "admin") return;
    api.get(`/admin/traffic?days=${trafficDays}`).then((r) => setTraffic(r.data)).catch(() => setTraffic({ total_visits: 0, sources: [], top_referrers: [], campaigns: [] }));
  }, [user, trafficDays]);

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
          <TabsTrigger value="traffic" data-testid="admin-tab-traffic">Traffic</TabsTrigger>
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

        {/* TRAFFIC SOURCES */}
        <TabsContent value="traffic">
          <div className="flex flex-wrap items-center justify-between gap-3 mb-6">
            <p className="text-sm text-muted-foreground">
              Where readers arrive from — first visit of each browser session, powered by referrers and UTM tags.
            </p>
            <Select value={trafficDays} onValueChange={setTrafficDays}>
              <SelectTrigger className="w-36" data-testid="admin-traffic-days-select">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="7">Last 7 days</SelectItem>
                <SelectItem value="30">Last 30 days</SelectItem>
                <SelectItem value="90">Last 90 days</SelectItem>
              </SelectContent>
            </Select>
          </div>
          {traffic === null ? (
            <Skeleton className="h-96 rounded-xl" />
          ) : traffic.total_visits === 0 ? (
            <Card className="rounded-xl">
              <CardContent className="py-16 text-center" data-testid="admin-traffic-empty">
                <Globe className="h-10 w-10 text-muted-foreground mx-auto mb-4" />
                <h3 className="font-serif text-xl font-semibold mb-2">No external visits yet</h3>
                <p className="text-sm text-muted-foreground max-w-md mx-auto">
                  When readers land here from LinkedIn, Instagram, Google, or your newsletter links,
                  their source shows up in this breakdown. Add <code className="font-mono text-xs">?utm_source=linkedin</code> to
                  links you share to attribute them precisely.
                </p>
              </CardContent>
            </Card>
          ) : (
            <>
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                <StatCard icon={Globe} label={`Visits (${traffic.days}d)`} value={traffic.total_visits} testId="admin-traffic-total" />
                <StatCard icon={TrendingUp} label="Top source" value={traffic.sources[0]?.source ?? "—"} testId="admin-traffic-top-source" />
                <StatCard icon={Users} label="Sources" value={traffic.sources.length} testId="admin-traffic-source-count" />
                <StatCard icon={Send} label="Campaigns" value={traffic.campaigns.length} testId="admin-traffic-campaign-count" />
              </div>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card className="rounded-xl lg:col-span-2">
                  <CardHeader><CardTitle className="font-serif text-xl">Weekly trend by source</CardTitle></CardHeader>
                  <CardContent className="h-72" data-testid="admin-traffic-trend-chart">
                    {traffic.trend?.length ? (
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={traffic.trend} margin={{ left: 0, right: 20, top: 5 }}>
                          <XAxis dataKey="week" tick={{ fontSize: 11 }} />
                          <YAxis allowDecimals={false} tick={{ fontSize: 11 }} width={32} />
                          <ReTooltip cursor={{ stroke: "hsla(168,52%,34%,0.2)" }} />
                          <Legend wrapperStyle={{ fontSize: 12 }} />
                          {(traffic.trend_series || []).map((s, i) => (
                            <Line
                              key={s}
                              type="monotone"
                              dataKey={s}
                              stroke={TREND_COLORS[i % TREND_COLORS.length]}
                              strokeWidth={2}
                              dot={{ r: 3 }}
                            />
                          ))}
                        </LineChart>
                      </ResponsiveContainer>
                    ) : (
                      <p className="text-sm text-muted-foreground pt-8 text-center" data-testid="admin-traffic-no-trend">
                        Trend appears once visits span more than one week.
                      </p>
                    )}
                  </CardContent>
                </Card>
                <Card className="rounded-xl">
                  <CardHeader><CardTitle className="font-serif text-xl">Visits by source</CardTitle></CardHeader>
                  <CardContent className="h-72" data-testid="admin-traffic-chart">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={traffic.sources} layout="vertical" margin={{ left: 10, right: 20 }}>
                        <XAxis type="number" hide />
                        <YAxis type="category" dataKey="source" width={110} tick={{ fontSize: 11 }} />
                        <ReTooltip cursor={{ fill: "hsla(168,52%,34%,0.06)" }} />
                        <Bar dataKey="count" fill="hsl(168 52% 34%)" radius={[0, 6, 6, 0]} barSize={18} />
                      </BarChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
                <Card className="rounded-xl">
                  <CardHeader><CardTitle className="font-serif text-xl">Source breakdown</CardTitle></CardHeader>
                  <CardContent className="p-0">
                    <Table data-testid="admin-traffic-sources-table">
                      <TableHeader>
                        <TableRow><TableHead>Source</TableHead><TableHead className="text-right">Visits</TableHead><TableHead className="text-right">Share</TableHead></TableRow>
                      </TableHeader>
                      <TableBody>
                        {traffic.sources.map((s) => (
                          <TableRow key={s.source} data-testid={`admin-traffic-source-${s.source.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`}>
                            <TableCell className="font-medium text-sm">{s.source}</TableCell>
                            <TableCell className="text-right font-mono text-sm">{s.count}</TableCell>
                            <TableCell className="text-right font-mono text-xs text-muted-foreground">{s.pct}%</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </CardContent>
                </Card>
                <Card className="rounded-xl">
                  <CardHeader><CardTitle className="font-serif text-xl">Top referring domains</CardTitle></CardHeader>
                  <CardContent className="p-0">
                    {traffic.top_referrers.length ? (
                      <Table data-testid="admin-traffic-referrers-table">
                        <TableHeader>
                          <TableRow><TableHead>Domain</TableHead><TableHead className="text-right">Visits</TableHead></TableRow>
                        </TableHeader>
                        <TableBody>
                          {traffic.top_referrers.map((r) => (
                            <TableRow key={r.host}>
                              <TableCell className="font-mono text-xs">{r.host}</TableCell>
                              <TableCell className="text-right font-mono text-sm">{r.count}</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    ) : (
                      <p className="text-sm text-muted-foreground p-6">No referrer domains recorded yet.</p>
                    )}
                  </CardContent>
                </Card>
                <Card className="rounded-xl">
                  <CardHeader><CardTitle className="font-serif text-xl">UTM campaigns</CardTitle></CardHeader>
                  <CardContent className="p-0">
                    {traffic.campaigns.length ? (
                      <Table data-testid="admin-traffic-campaigns-table">
                        <TableHeader>
                          <TableRow><TableHead>Campaign</TableHead><TableHead>Source</TableHead><TableHead className="text-right">Visits</TableHead></TableRow>
                        </TableHeader>
                        <TableBody>
                          {traffic.campaigns.map((c, i) => (
                            <TableRow key={`${c.campaign}-${i}`}>
                              <TableCell className="font-medium text-sm">{c.campaign}</TableCell>
                              <TableCell><Badge variant="secondary" className="font-mono text-[10px]">{c.source}</Badge></TableCell>
                              <TableCell className="text-right font-mono text-sm">{c.count}</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    ) : (
                      <p className="text-sm text-muted-foreground p-6" data-testid="admin-traffic-no-campaigns">
                        No UTM campaigns yet. Share links like <code className="font-mono text-xs">?utm_source=linkedin&utm_campaign=launch</code> to track them.
                      </p>
                    )}
                  </CardContent>
                </Card>
              </div>
            </>
          )}
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
