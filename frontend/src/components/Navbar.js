import { useState } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";
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
import { Moon, Sun, Menu, Crown, LayoutDashboard, User, LogOut, Archive, Bookmark } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { NotificationsBell } from "@/components/NotificationsBell";
import { useTheme } from "@/context/ThemeContext";
import { CATEGORIES } from "@/lib/api";

export const Navbar = () => {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);

  const navLinkCls = ({ isActive }) =>
    `text-sm transition-colors duration-150 ${isActive ? "text-accent font-medium" : "text-muted-foreground hover:text-foreground"}`;

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
                <img src="/logo192.png" alt="The Trading Narrative logo" className="w-8 h-8" />
                <span className="font-serif text-xl font-semibold">The Trading Narrative</span>
              </div>
              <nav className="flex flex-col gap-4">
                {CATEGORIES.map((c) => (
                  <Link
                    key={c.slug}
                    to={`/category/${c.slug}`}
                    onClick={() => setOpen(false)}
                    className="text-base text-foreground hover:text-accent transition-colors"
                    data-testid={`nav-mobile-category-${c.slug}`}
                  >
                    {c.label}
                  </Link>
                ))}
                <div className="h-px bg-border my-1" />
                <Link to="/archive" onClick={() => setOpen(false)} className="text-base hover:text-accent">Archive</Link>
                <Link to="/briefings" onClick={() => setOpen(false)} className="text-base hover:text-accent" data-testid="nav-mobile-briefings-link">Briefings</Link>
                <Link to="/lounge" onClick={() => setOpen(false)} className="text-base hover:text-accent" data-testid="nav-mobile-lounge-link">Lounge</Link>
                <Link to="/pricing" onClick={() => setOpen(false)} className="text-base hover:text-accent">Pricing</Link>
                <Link to="/about" onClick={() => setOpen(false)} className="text-base hover:text-accent">About</Link>
              </nav>
            </SheetContent>
          </Sheet>

          <Link to="/" className="flex items-center gap-2.5" data-testid="nav-logo">
            <img src="/logo192.png" alt="The Trading Narrative logo" className="w-9 h-9 sm:w-10 sm:h-10 shrink-0" />
            <span className="font-serif text-lg sm:text-xl font-semibold tracking-tight">
              The Trading Narrative
            </span>
          </Link>
        </div>

        <nav className="hidden lg:flex items-center gap-6">
          {CATEGORIES.map((c) => (
            <NavLink key={c.slug} to={`/category/${c.slug}`} className={navLinkCls} data-testid={`nav-category-${c.slug}`}>
              {c.label}
            </NavLink>
          ))}
          <NavLink to="/archive" className={navLinkCls} data-testid="nav-archive-link">
            Archive
          </NavLink>
          <NavLink to="/briefings" className={navLinkCls} data-testid="nav-briefings-link">
            Briefings
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
