{
  "brand": {
    "name": "The Trading Narrative",
    "positioning": "Personal-brand publication that feels like a premium magazine + modern newsletter (Substack utility, magazine craft).",
    "audience": "Professionals/aspiring investors & creators (25–45), mobile-first from LinkedIn/Instagram.",
    "brand_attributes": [
      "trustworthy",
      "editorial",
      "calm premium",
      "sharp + analytical",
      "human + personal"
    ],
    "visual_style_fusion": {
      "layout_principle": "Swiss editorial grid + magazine modules (rules, section labels, asymmetry).",
      "typography_personality": "High-contrast serif headlines (magazine) + neutral sans body (newsletter clarity).",
      "surface_style": "Paper-like light background with subtle grain; crisp borders; minimal shadows.",
      "motion_style": "Subtle scroll reveals + micro-interactions; no flashy effects; reading-first."
    }
  },

  "design_tokens": {
    "notes": "One accent color only. Use it for CTAs, active states, links, and premium indicators. Keep everything else neutral. Avoid gradients except tiny decorative overlays (<20% viewport).",

    "css_custom_properties": {
      "how_to_apply": "Update /app/frontend/src/index.css :root and .dark variables to match these HSL tokens. Keep shadcn variable names; only change values.",
      "light": {
        "--background": "40 33% 98%",
        "--foreground": "222 22% 12%",

        "--card": "0 0% 100%",
        "--card-foreground": "222 22% 12%",

        "--popover": "0 0% 100%",
        "--popover-foreground": "222 22% 12%",

        "--primary": "222 22% 12%",
        "--primary-foreground": "40 33% 98%",

        "--secondary": "40 18% 95%",
        "--secondary-foreground": "222 22% 12%",

        "--muted": "40 18% 95%",
        "--muted-foreground": "222 10% 42%",

        "--accent": "168 52% 34%",
        "--accent-foreground": "0 0% 100%",

        "--destructive": "0 72% 52%",
        "--destructive-foreground": "0 0% 100%",

        "--border": "40 12% 88%",
        "--input": "40 12% 88%",
        "--ring": "168 52% 34%",

        "--radius": "0.75rem"
      },
      "dark": {
        "--background": "222 22% 8%",
        "--foreground": "40 33% 96%",

        "--card": "222 22% 10%",
        "--card-foreground": "40 33% 96%",

        "--popover": "222 22% 10%",
        "--popover-foreground": "40 33% 96%",

        "--primary": "40 33% 96%",
        "--primary-foreground": "222 22% 10%",

        "--secondary": "222 16% 14%",
        "--secondary-foreground": "40 33% 96%",

        "--muted": "222 16% 14%",
        "--muted-foreground": "40 10% 70%",

        "--accent": "168 52% 40%",
        "--accent-foreground": "222 22% 8%",

        "--destructive": "0 62% 42%",
        "--destructive-foreground": "0 0% 100%",

        "--border": "222 14% 18%",
        "--input": "222 14% 18%",
        "--ring": "168 52% 40%",

        "--radius": "0.75rem"
      },
      "additional_tokens_add_to_index_css": {
        "--container-max": "72rem",
        "--reading-max": "42rem",
        "--shadow-soft": "0 10px 30px rgba(15, 23, 42, 0.06)",
        "--shadow-float": "0 18px 50px rgba(15, 23, 42, 0.10)",
        "--hairline": "1px",
        "--noise-opacity": "0.06"
      }
    },

    "tailwind_usage": {
      "accent_color_rule": "Use accent ONLY via text-accent, bg-accent, ring-accent, border-accent, and link underline decoration-accent/40. Do not introduce additional brand colors.",
      "backgrounds": [
        "bg-background",
        "bg-card",
        "bg-muted/40 (section wash)",
        "dark:bg-background"
      ],
      "borders": [
        "border-border",
        "border-border/70",
        "divide-border"
      ]
    }
  },

  "typography": {
    "font_pairing": {
      "headlines": {
        "google_font": "EB Garamond",
        "fallback": "ui-serif, Georgia, Cambria, Times New Roman, Times, serif",
        "usage": "Hero headline, article titles, section headers, pricing plan names"
      },
      "body_ui": {
        "google_font": "Figtree",
        "fallback": "ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial",
        "usage": "Body copy, nav, buttons, forms, admin UI"
      },
      "mono_optional": {
        "google_font": "IBM Plex Mono",
        "usage": "Read time, tags, metadata, admin table numbers"
      }
    },
    "implementation_notes_js": {
      "google_fonts": "Use <link> tags in public/index.html or import in index.css. Then set body font-family to Figtree and apply a .font-serif utility class for EB Garamond headings.",
      "reading_defaults": [
        "Article body uses leading-7 md:leading-8",
        "Max line length: max-w-[var(--reading-max)]",
        "Use prose classes carefully; avoid over-styling links"
      ]
    },
    "type_scale": {
      "h1": "text-4xl sm:text-5xl lg:text-6xl",
      "h2": "text-base md:text-lg",
      "body": "text-sm md:text-base",
      "small": "text-xs md:text-sm",
      "meta": "text-xs tracking-wide uppercase"
    },
    "editorial_rules": [
      "Use serif only for headlines and pull quotes; keep body sans for long reading comfort.",
      "Use hairline separators (Separator component) to create magazine rhythm.",
      "Use section labels (meta style) above modules: FEATURED, LATEST, FINANCE, etc."
    ]
  },

  "layout_and_grid": {
    "global_container": {
      "max_width": "max-w-[var(--container-max)]",
      "padding": "px-4 sm:px-6 lg:px-8",
      "rhythm": "Use py-10 sm:py-14 for major sections; gap-8+ between modules"
    },
    "homepage": {
      "hero": {
        "pattern": "Two-column on lg: left editorial headline + dek + CTAs; right featured cover image card.",
        "mobile": "Stacked: headline -> dek -> subscribe form -> featured card.",
        "details": [
          "Add a thin rule under hero (Separator) to signal magazine structure.",
          "Use a small accent dot or rule as a signature motif (e.g., a 6px accent square next to section labels)."
        ]
      },
      "featured_latest": {
        "pattern": "Featured post as large card; latest posts as a vertical list with small thumbnails and read time.",
        "components": ["Card", "AspectRatio", "Badge", "Separator"]
      },
      "filterable_grid": {
        "pattern": "Tabs for categories + responsive grid (1 col mobile, 2 col md, 3 col xl).",
        "interaction": "Tabs sticky on scroll within section on mobile (optional).",
        "components": ["Tabs", "Card", "Badge", "Pagination"]
      },
      "newsletter_block": {
        "pattern": "Full-width muted wash section with a centered card inside (NOT centered page layout; just centered module).",
        "cta": "Single primary CTA: Subscribe",
        "components": ["Card", "Input", "Button"]
      }
    },
    "article_page": {
      "reading_layout": {
        "pattern": "Centered reading column with left rail share bar on lg.",
        "max_width": "max-w-[var(--reading-max)]",
        "cover_image": "Full-bleed within container using negative margins on lg only (magazine feel).",
        "components": ["Separator", "Badge", "Avatar", "Tooltip"]
      },
      "related_posts": {
        "pattern": "3-up grid on desktop, carousel on mobile if needed.",
        "components": ["Card", "Carousel"]
      }
    },
    "admin": {
      "pattern": "Dashboard with left nav (Sheet on mobile) + content area with stats cards and tables.",
      "components": ["Sheet", "NavigationMenu", "Card", "Table", "Tabs", "Dialog"]
    }
  },

  "components": {
    "component_path": {
      "shadcn_primary": "/app/frontend/src/components/ui/",
      "use_components": [
        {"name": "button", "path": "/app/frontend/src/components/ui/button.jsx"},
        {"name": "input", "path": "/app/frontend/src/components/ui/input.jsx"},
        {"name": "card", "path": "/app/frontend/src/components/ui/card.jsx"},
        {"name": "badge", "path": "/app/frontend/src/components/ui/badge.jsx"},
        {"name": "tabs", "path": "/app/frontend/src/components/ui/tabs.jsx"},
        {"name": "separator", "path": "/app/frontend/src/components/ui/separator.jsx"},
        {"name": "avatar", "path": "/app/frontend/src/components/ui/avatar.jsx"},
        {"name": "tooltip", "path": "/app/frontend/src/components/ui/tooltip.jsx"},
        {"name": "dropdown-menu", "path": "/app/frontend/src/components/ui/dropdown-menu.jsx"},
        {"name": "switch", "path": "/app/frontend/src/components/ui/switch.jsx"},
        {"name": "dialog", "path": "/app/frontend/src/components/ui/dialog.jsx"},
        {"name": "sheet", "path": "/app/frontend/src/components/ui/sheet.jsx"},
        {"name": "table", "path": "/app/frontend/src/components/ui/table.jsx"},
        {"name": "textarea", "path": "/app/frontend/src/components/ui/textarea.jsx"},
        {"name": "calendar", "path": "/app/frontend/src/components/ui/calendar.jsx"},
        {"name": "sonner", "path": "/app/frontend/src/components/ui/sonner.jsx"}
      ]
    },

    "navigation": {
      "top_nav": {
        "pattern": "Left: wordmark. Center (desktop): category links. Right: Search, Dark mode toggle, Account/Premium badge.",
        "mobile": "Hamburger opens Sheet with categories + pricing + about + archive.",
        "premium_badge": "Use Badge variant with accent border/text; show only for subscribers.",
        "data_testids": {
          "dark_mode_toggle": "dark-mode-toggle",
          "nav_subscribe_button": "nav-subscribe-button",
          "nav_premium_badge": "nav-premium-badge",
          "nav_mobile_menu_button": "nav-mobile-menu-button"
        }
      }
    },

    "buttons": {
      "style": "Luxury / Elegant (rounded 10–12px, subtle elevation).",
      "variants": {
        "primary": "bg-accent text-accent-foreground hover:bg-accent/90 focus-visible:ring-2 focus-visible:ring-ring",
        "secondary": "bg-secondary text-secondary-foreground hover:bg-secondary/70",
        "ghost": "hover:bg-muted/60"
      },
      "micro_interactions": [
        "Hover: translate-y-[-1px] + shadow-soft (only on primary CTA).",
        "Active: scale-[0.98].",
        "Focus: visible ring using --ring (accent)."
      ],
      "data_testids": {
        "primary_cta": "primary-cta-button",
        "newsletter_submit": "newsletter-submit-button",
        "paywall_upgrade": "paywall-upgrade-button"
      }
    },

    "forms": {
      "newsletter_capture": {
        "pattern": "Email input + primary button; optional name field hidden behind Collapsible on desktop.",
        "validation": "Inline error text below input; use Alert for submission errors.",
        "data_testids": {
          "email_input": "newsletter-email-input",
          "inline_form": "newsletter-inline-form"
        }
      },
      "auth": {
        "pattern": "Tabs: Password / Magic Link. Keep it minimal and editorial.",
        "components": ["Tabs", "Card", "Input", "Button"],
        "data_testids": {
          "login_tab_password": "login-tab-password",
          "login_tab_magic": "login-tab-magic",
          "login_submit": "login-submit-button"
        }
      }
    },

    "article_cards": {
      "card_style": "White card with hairline border; image with AspectRatio; metadata row (category badge + read time).",
      "hover": "Border darkens slightly + image subtle zoom (scale-105) with overflow-hidden.",
      "data_testids": {
        "article_card": "article-card",
        "article_card_title": "article-card-title"
      }
    },

    "paywall": {
      "pattern": "After 2–3 paragraphs: fade + blur overlay with Upgrade CTA card.",
      "implementation": {
        "css": [
          "Wrap premium content in a container with max-h and overflow-hidden.",
          "Add ::after gradient fade (light) or dark overlay (dark mode).",
          "Apply filter: blur(6px) to the truncated portion only (not the CTA)."
        ],
        "cta_card": "Card with plan highlights + button + trust copy (cancel anytime).",
        "data_testids": {
          "paywall_container": "paywall-container",
          "paywall_blurred_content": "paywall-blurred-content",
          "paywall_cta": "paywall-cta"
        }
      }
    },

    "pricing": {
      "toggle": {
        "component": "Switch",
        "default": "Annual (show savings pill)",
        "data_testids": {
          "pricing_toggle": "pricing-billing-toggle",
          "pricing_toggle_monthly": "pricing-billing-monthly",
          "pricing_toggle_annual": "pricing-billing-annual"
        }
      },
      "tier_cards": {
        "pattern": "Two cards (Free vs Premium) with Premium highlighted via subtle accent border + small 'Most Popular' badge.",
        "comparison": "Below cards: Table with grouped features.",
        "data_testids": {
          "pricing_free_card": "pricing-free-card",
          "pricing_premium_card": "pricing-premium-card",
          "pricing_checkout_button": "pricing-checkout-button"
        }
      }
    },

    "social_share": {
      "pattern": "Sticky share rail on lg; bottom sheet share on mobile.",
      "actions": [
        "LinkedIn share",
        "Copy link (Instagram) -> toast",
        "Download IG story/post card",
        "Web Share API when available"
      ],
      "components": ["Tooltip", "Button", "Drawer", "Sonner"],
      "data_testids": {
        "share_linkedin": "share-linkedin-button",
        "share_copy_link": "share-copy-link-button",
        "share_download_ig": "share-download-ig-button",
        "share_web": "share-webshare-button"
      }
    },

    "archive_search": {
      "pattern": "Search input + category/tier filters + results list with pagination.",
      "components": ["Input", "Select", "Badge", "Pagination"],
      "data_testids": {
        "archive_search_input": "archive-search-input",
        "archive_category_filter": "archive-category-filter",
        "archive_tier_filter": "archive-tier-filter"
      }
    },

    "admin_cms": {
      "posts_table": {
        "components": ["Table", "DropdownMenu", "Badge"],
        "columns": ["Title", "Category", "Tier", "Status", "Publish date", "Actions"],
        "data_testids": {
          "admin_posts_table": "admin-posts-table",
          "admin_new_post": "admin-new-post-button"
        }
      },
      "post_editor": {
        "pattern": "Title + dek + cover image URL + category select + tier select + schedule (Calendar in Popover) + body (Textarea or rich text later).",
        "components": ["Input", "Textarea", "Select", "Popover", "Calendar", "Button"],
        "data_testids": {
          "admin_post_title": "admin-post-title-input",
          "admin_post_publish": "admin-post-publish-button",
          "admin_post_schedule": "admin-post-schedule-button"
        }
      },
      "analytics": {
        "library": "recharts",
        "charts": ["Subscribers growth line", "Top posts bar"],
        "data_testids": {
          "admin_analytics_subscribers_chart": "admin-analytics-subscribers-chart",
          "admin_analytics_top_posts_chart": "admin-analytics-top-posts-chart"
        }
      }
    }
  },

  "motion_and_microinteractions": {
    "library": "framer-motion",
    "install": {
      "command": "npm i framer-motion",
      "usage": "Use motion.div for section entrance (opacity + y). Respect prefers-reduced-motion."
    },
    "principles": [
      "Entrance: 12–16px y + fade in; stagger lists by 0.04–0.06s.",
      "Hover: only on cards/buttons; keep subtle.",
      "Scroll: optional progress indicator on article page (Progress component) but keep minimal.",
      "Never animate layout shifts that affect reading (avoid big parallax in article body)."
    ],
    "durations": {
      "fast": "150ms",
      "base": "220ms",
      "slow": "320ms"
    },
    "easings": {
      "standard": "cubic-bezier(0.2, 0.8, 0.2, 1)",
      "snappy": "cubic-bezier(0.2, 0.9, 0.2, 1)"
    }
  },

  "textures_and_gradients": {
    "grain": {
      "rule": "Use a subtle noise overlay across the background only (opacity <= var(--noise-opacity)).",
      "implementation": "Add a fixed pseudo-element on body or a top-level layout wrapper with background-image: url(noise) and mix-blend-mode: multiply; pointer-events none.",
      "image_url": "https://images.unsplash.com/photo-1604147706283-d7119b5b822c?crop=entropy&cs=srgb&fm=jpg&ixlib=rb-4.1.0&q=85"
    },
    "gradients": {
      "allowed_usage": "Decorative overlay in hero only (<=20% viewport).",
      "safe_gradient": "radial-gradient(600px circle at 20% 10%, hsla(168,52%,34%,0.10), transparent 55%)",
      "restriction": "No saturated/dark gradients; never on text-heavy areas; never on small elements."
    }
  },

  "image_urls": {
    "hero_cover_options": [
      {
        "category": "hero",
        "description": "Minimal travel landscape with lots of negative space (works with editorial headline).",
        "url": "https://images.unsplash.com/photo-1708162426274-514093c95e0d?crop=entropy&cs=srgb&fm=jpg&ixlib=rb-4.1.0&q=85"
      },
      {
        "category": "hero",
        "description": "Minimal field landscape; use as featured post cover.",
        "url": "https://images.unsplash.com/photo-1545472956-3ebf777846cc?crop=entropy&cs=srgb&fm=jpg&ixlib=rb-4.1.0&q=85"
      }
    ],
    "author_portrait_options": [
      {
        "category": "about/author",
        "description": "Editorial portrait with newspaper vibe (fits magazine brand).",
        "url": "https://images.pexels.com/photos/38894194/pexels-photo-38894194.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940"
      },
      {
        "category": "about/author",
        "description": "Neutral studio portrait; calm premium tone.",
        "url": "https://images.pexels.com/photos/10209456/pexels-photo-10209456.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940"
      }
    ],
    "texture_backgrounds": [
      {
        "category": "texture",
        "description": "Paper/plaster texture for subtle grain overlay.",
        "url": "https://images.unsplash.com/photo-1615800098779-1be32e60cca3?crop=entropy&cs=srgb&fm=jpg&ixlib=rb-4.1.0&q=85"
      }
    ]
  },

  "performance": {
    "image_rules": [
      "Use responsive sizes and lazy loading for non-hero images.",
      "Prefer Unsplash URLs with q=80–85 and explicit width params.",
      "Avoid background images for content; use <img> with object-cover."
    ],
    "ui_rules": [
      "Avoid heavy shadows everywhere; reserve for hover/featured modules.",
      "Keep admin charts lightweight; render skeletons while loading."
    ]
  },

  "accessibility": {
    "requirements": [
      "WCAG AA contrast for text and interactive elements.",
      "Visible focus states (ring).",
      "Respect prefers-reduced-motion (disable entrance animations).",
      "Tap targets >= 44px on mobile.",
      "Use semantic headings order on article pages."
    ],
    "content_readability": [
      "Line length capped at ~70–75 characters (reading max).",
      "Use sufficient leading (leading-7/8).",
      "Avoid justified text; left align."
    ]
  },

  "instructions_to_main_agent": {
    "cleanup_existing_css": [
      "Remove CRA demo styles from /app/frontend/src/App.css (App-header centering etc). Keep file minimal or delete unused classes.",
      "Implement the token updates in /app/frontend/src/index.css only; keep shadcn variable names."
    ],
    "dark_mode": [
      "Use the existing .dark class strategy (toggle on <html> or <body>).",
      "Persist preference in localStorage; default to system preference."
    ],
    "data_testid_policy": "Every interactive element and key informational element must include data-testid in kebab-case (buttons, links, inputs, toggles, badges showing premium status, error banners, pricing amounts, etc.).",
    "page_specific_notes": {
      "home": [
        "Hero includes newsletter capture (email + CTA) and a featured post card.",
        "Category filter uses Tabs; keep accent only on active tab underline or pill border."
      ],
      "article": [
        "Use a left share rail on lg and a bottom Drawer on mobile.",
        "Paywall blur/fade must feel premium: blur only the truncated content; CTA stays crisp."
      ],
      "pricing": [
        "Annual default; show savings badge near toggle.",
        "Premium plan card gets subtle accent border + 'Most Popular' badge."
      ],
      "admin": [
        "Use Table + DropdownMenu for row actions.",
        "Use Calendar for scheduling (Popover + Calendar)."
      ]
    },
    "libraries": {
      "icons": "Use lucide-react (preferred) or FontAwesome CDN; no emoji icons.",
      "toasts": "Use Sonner (/app/frontend/src/components/ui/sonner.jsx).",
      "charts": "Install recharts for admin analytics: npm i recharts",
      "motion": "Install framer-motion for subtle entrance animations: npm i framer-motion"
    }
  },

  "general_ui_ux_design_guidelines": "<General UI UX Design Guidelines>  \n    - You must **not** apply universal transition. Eg: `transition: all`. This results in breaking transforms. Always add transitions for specific interactive elements like button, input excluding transforms\n    - You must **not** center align the app container, ie do not add `.App { text-align: center; }` in the css file. This disrupts the human natural reading flow of text\n   - NEVER: use AI assistant Emoji characters like`🤖🧠💭💡🔮🎯📚🎭🎬🎪🎉🎊🎁🎀🎂🍰🎈🎨🎰💰💵💳🏦💎🪙💸🤑📊📈📉💹🔢🏆🥇 etc for icons. Always use **FontAwesome cdn** or **lucid-react** library already installed in the package.json\n\n **GRADIENT RESTRICTION RULE**\nNEVER use dark/saturated gradient combos (e.g., purple/pink) on any UI element.  Prohibited gradients: blue-500 to purple 600, purple 500 to pink-500, green-500 to blue-500, red to pink etc\nNEVER use dark gradients for logo, testimonial, footer etc\nNEVER let gradients cover more than 20% of the viewport.\nNEVER apply gradients to text-heavy content or reading areas.\nNEVER use gradients on small UI elements (<100px width).\nNEVER stack multiple gradient layers in the same viewport.\n\n**ENFORCEMENT RULE:**\n    • Id gradient area exceeds 20% of viewport OR affects readability, **THEN** use solid colors\n\n**How and where to use:**\n   • Section backgrounds (not content backgrounds)\n   • Hero section header content. Eg: dark to light to dark color\n   • Decorative overlays and accent elements only\n   • Hero section with 2-3 mild color\n   • Gradients creation can be done for any angle say horizontal, vertical or diagonal\n\n- For AI chat, voice application, **do not use purple color. Use color like light green, ocean blue, peach orange etc**\n\n</Font Guidelines>\n\n- Every interaction needs micro-animations - hover states, transitions, parallax effects, and entrance animations. Static = dead. \n   \n- Use 2-3x more spacing than feels comfortable. Cramped designs look cheap.\n\n- Subtle grain textures, noise overlays, custom cursors, selection states, and loading animations: separates good from extraordinary.\n   \n- Before generating UI, infer the visual style from the problem statement (palette, contrast, mood, motion) and immediately instantiate it by setting global design tokens (primary, secondary/accent, background, foreground, ring, state colors), rather than relying on any library defaults. Don't make the background dark as a default step, always understand problem first and define colors accordingly\n    Eg: - if it implies playful/energetic, choose a colorful scheme\n           - if it implies monochrome/minimal, choose a black–white/neutral scheme\n\n**Component Reuse:**\n\t- Prioritize using pre-existing components from src/components/ui when applicable\n\t- Create new components that match the style and conventions of existing components when needed\n\t- Examine existing components to understand the project's component patterns before creating new ones\n\n**IMPORTANT**: Do not use HTML based component like dropdown, calendar, toast etc. You **MUST** always use `/app/frontend/src/components/ui/ ` only as a primary components as these are modern and stylish component\n\n**Best Practices:**\n\t- Use Shadcn/UI as the primary component library for consistency and accessibility\n\t- Import path: ./components/[component-name]\n\n**Export Conventions:**\n\t- Components MUST use named exports (export const ComponentName = ...)\n\t- Pages MUST use default exports (export default function PageName() {...})\n\n**Toasts:**\n  - Use `sonner` for toasts\"\n  - Sonner component are located in `/app/src/components/ui/sonner.tsx`\n\nUse 2–4 color gradients, subtle textures/noise overlays, or CSS-based noise to avoid flat visuals.\n</General UI UX Design Guidelines>"
}
