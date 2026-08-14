import { useRef, useState } from "react";
import { Link, NavLink, useLocation, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { pillarAccent, PILLAR_TAGLINES } from "@/lib/pillars";
import { Moon, Sun, Menu, Crown, LayoutDashboard, User, LogOut, Archive, Bookmark, Highlighter, Flame, ChevronDown, Columns3 } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { NotificationsBell } from "@/components/NotificationsBell";
import { useTheme } from "@/context/ThemeContext";
import { CATEGORIES } from "@/lib/api";

export const Navbar = () => {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const location = useLocation();
  const [open, setOpen] = useState(false);
  const [pillarsOpen, setPillarsOpen] = useState(false);
  const closeTimer = useRef(null);

  const openPillars = () => {
    if (closeTimer.current) clearTimeout(closeTimer.current);
    setPillarsOpen(true);
  };
  const closePillarsSoon = () => {
    if (closeTimer.current) clearTimeout(closeTimer.current);
    closeTimer.current = setTimeout(() => setPillarsOpen(false), 150);
  };

  const onPillarPage = location.pathname.startsWith("/category/");

  const navLinkCls = ({ isActive }) =>
    `text-sm whitespace-nowrap transition-colors duration-150 ${isActive ? "text-accent font-medium" : "text-muted-foreground hover:text-foreground"}`;

  return (
    <header className="sticky top-0 z-50 bg-background/85 backdrop-blur-md border-b border-border">
      <div className="container-editorial flex items-center justify-between h-16">
        <div className="flex items-center gap-3">
          <Sheet open={open} onOpenChange={setOpen}>
            <SheetTrigger asChild className="lg:hidden">
              <Button variant="ghost" size="icon" data-testid="nav-mobile-menu-button" aria-label="Menu">
                <Menu className="h-5 w-5" />
              </Button>
            </SheetTrigger>
            <SheetContent side="left" className="w-72">
              <div className="flex items-center gap-2 mt-2 mb-6">
                <img src="/logo192.png" alt="The Trading Narrative logo" className="w-8 h-8 animate-[spin_9s_linear_infinite] motion-reduce:animate-none" />
                <span className="font-serif text-xl font-semibold">The Trading Narrative</span>
              </div>
              <nav className="flex flex-col gap-4">
                <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground inline-flex items-center gap-1.5">
                  <Columns3 className="h-3 w-3" /> Pillars
                </span>
                {CATEGORIES.map((c) => (
                  <Link
                    key={c.slug}
                    to={`/category/${c.slug}`}
                    onClick={() => setOpen(false)}
                    className="text-base text-foreground hover:text-accent transition-colors"
                    data-testid={`nav-mobile-category-${c.slug}`}
                  >
                    <span className="inline-flex items-center gap-2">
                      <span className="inline-block h-2 w-2 rounded-full shrink-0" style={{ backgroundColor: pillarAccent(c.slug) }} aria-hidden />
                      {c.label}
                    </span>
                  </Link>
                ))}
                <div className="h-px bg-border my-1" />
                <Link to="/archive" onClick={() => setOpen(false)} className="text-base hover:text-accent">Archive</Link>
                <Link to="/briefings" onClick={() => setOpen(false)} className="text-base hover:text-accent" data-testid="nav-mobile-briefings-link">Briefings</Link>
                <Link to="/books" onClick={() => setOpen(false)} className="text-base hover:text-accent" data-testid="nav-mobile-books-link">Books</Link>
                <Link to="/lounge" onClick={() => setOpen(false)} className="text-base hover:text-accent" data-testid="nav-mobile-lounge-link">Lounge</Link>
                <Link to="/pricing" onClick={() => setOpen(false)} className="text-base hover:text-accent">Pricing</Link>
                <Link to="/about" onClick={() => setOpen(false)} className="text-base hover:text-accent">About</Link>
              </nav>
            </SheetContent>
          </Sheet>

          <Link to="/" className="flex items-center gap-2.5" data-testid="nav-logo">
            <img src="/logo192.png" alt="The Trading Narrative logo" className="w-9 h-9 sm:w-10 sm:h-10 shrink-0 animate-[spin_9s_linear_infinite] motion-reduce:animate-none" />
            <span className="font-serif text-lg sm:text-xl font-semibold tracking-tight">
              The Trading Narrative
            </span>
          </Link>
        </div>

        <nav className="hidden lg:flex items-center gap-6">
          <DropdownMenu open={pillarsOpen} onOpenChange={setPillarsOpen} modal={false}>
            <DropdownMenuTrigger asChild>
              <button
                type="button"
                onMouseEnter={openPillars}
                onMouseLeave={closePillarsSoon}
                className={`inline-flex items-center gap-1 text-sm whitespace-nowrap transition-colors duration-150 focus:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded-sm ${
                  onPillarPage ? "text-accent font-medium" : "text-muted-foreground hover:text-foreground"
                }`}
                data-testid="nav-pillars-trigger"
                aria-label="Browse pillars"
              >
                Pillars
                <ChevronDown className={`h-3.5 w-3.5 transition-transform duration-150 ${pillarsOpen ? "rotate-180" : ""}`} />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent
              align="start"
              sideOffset={10}
              className="w-80"
              onMouseEnter={openPillars}
              onMouseLeave={closePillarsSoon}
              data-testid="nav-pillars-dropdown"
            >
              {CATEGORIES.map((c) => (
                <DropdownMenuItem
                  key={c.slug}
                  className="py-2.5 cursor-pointer"
                  onClick={() => { setPillarsOpen(false); navigate(`/category/${c.slug}`); }}
                  data-testid={`nav-category-${c.slug}`}
                >
                  <span className="mt-1 inline-block h-2 w-2 rounded-full shrink-0 self-start" style={{ backgroundColor: pillarAccent(c.slug) }} aria-hidden />
                  <span className="ml-2.5 min-w-0">
                    <span className="block text-sm font-medium text-foreground">{c.label}</span>
                    {PILLAR_TAGLINES[c.slug] && (
                      <span className="block text-xs text-muted-foreground leading-snug mt-0.5">{PILLAR_TAGLINES[c.slug]}</span>
                    )}
                  </span>
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>
          <NavLink to="/archive" className={navLinkCls} data-testid="nav-archive-link">
            Archive
          </NavLink>
          <NavLink to="/briefings" className={navLinkCls} data-testid="nav-briefings-link">
            Briefings
          </NavLink>
          <NavLink to="/books" className={navLinkCls} data-testid="nav-books-link">
            Books
          </NavLink>
          <NavLink to="/lounge" className={navLinkCls} data-testid="nav-lounge-link">
            Lounge
          </NavLink>
          <NavLink to="/about" className={navLinkCls} data-testid="nav-about-link">
            About
          </NavLink>
        </nav>

        <div className="flex items-center gap-2">
          <NotificationsBell />
          <Button variant="ghost" size="icon" onClick={toggleTheme} data-testid="dark-mode-toggle" aria-label="Toggle dark mode">
            {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </Button>

          {user && (user.current_streak || 0) > 0 && (
            <Badge
              variant="secondary"
              className="hidden sm:inline-flex items-center gap-1 rounded-md font-mono text-[11px] tabular-nums cursor-default"
              title={`${user.current_streak}-day reading streak, longest: ${user.longest_streak || user.current_streak} days`}
              data-testid="nav-streak-counter"
            >
              <Flame className="h-3 w-3 text-accent" /> {user.current_streak}
            </Badge>
          )}

          {user?.is_premium && (
            <Badge className="hidden sm:inline-flex bg-accent/10 text-accent border border-accent/30 hover:bg-accent/10 gap-1 rounded-md" data-testid="nav-premium-badge">
              <Crown className="h-3 w-3" /> Premium
            </Badge>
          )}

          {!user?.is_premium && (
            <Button
              onClick={() => navigate("/pricing")}
              className="hidden sm:inline-flex bg-accent text-accent-foreground hover:bg-accent/90 h-9"
              data-testid="nav-subscribe-button"
            >
              Go Premium
            </Button>
          )}

          {user ? (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button className="rounded-full focus:outline-none focus-visible:ring-2 focus-visible:ring-ring" data-testid="nav-account-menu">
                  <Avatar className="h-8 w-8 border border-border">
                    <AvatarFallback className="bg-secondary text-xs font-medium">
                      {(user.name || user.email || "U").slice(0, 2).toUpperCase()}
                    </AvatarFallback>
                  </Avatar>
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-52">
                <DropdownMenuLabel className="truncate">{user.name || user.email}</DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => navigate("/account")} data-testid="nav-account-link">
                  <User className="h-4 w-4 mr-2" /> Account & Billing
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => navigate("/reading-list")} data-testid="nav-reading-list-link">
                  <Bookmark className="h-4 w-4 mr-2" /> Reading List
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => navigate("/highlights")} data-testid="nav-highlights-link">
                  <Highlighter className="h-4 w-4 mr-2" /> Highlights
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => navigate("/archive")}>
                  <Archive className="h-4 w-4 mr-2" /> Archive
                </DropdownMenuItem>
                {user.role === "admin" && (
                  <DropdownMenuItem onClick={() => navigate("/admin")} data-testid="nav-admin-link">
                    <LayoutDashboard className="h-4 w-4 mr-2" /> Admin Studio
                  </DropdownMenuItem>
                )}
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => { logout(); navigate("/"); }} data-testid="nav-logout-button">
                  <LogOut className="h-4 w-4 mr-2" /> Sign out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          ) : (
            <Button variant="ghost" onClick={() => navigate("/auth")} className="h-9" data-testid="nav-signin-button">
              Sign in
            </Button>
          )}
        </div>
      </div>
    </header>
  );
};
