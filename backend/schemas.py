"""Pydantic request schemas."""
from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    name: str = Field(min_length=1, max_length=80)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class MagicRequestIn(BaseModel):
    email: EmailStr


class MagicVerifyIn(BaseModel):
    token: str


class CheckoutIn(BaseModel):
    plan: str  # monthly | annual
    origin_url: Optional[str] = None


class PasswordResetRequestIn(BaseModel):
    email: EmailStr


class PasswordResetConfirmIn(BaseModel):
    token: str
    password: str = Field(min_length=6)


class CommentIn(BaseModel):
    body: str = Field(min_length=1, max_length=2000)
    parent_id: Optional[str] = None


class BookmarkToggleIn(BaseModel):
    post_id: str


class NewsletterIn(BaseModel):
    email: EmailStr
    source: str = 'site'


class PostIn(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    excerpt: str = ''
    category: str
    tier: str = 'free'
    cover_image: str = ''
    content_blocks: List[str] = []
    tags: List[str] = []
    featured: bool = False
    status: str = 'draft'  # draft | published | scheduled
    publish_at: Optional[str] = None
    edition: Optional[int] = None  # newsletter edition number for weekly briefings


class IssueIn(BaseModel):
    post_id: str
    subject: Optional[str] = None


class TrackIn(BaseModel):
    event: str
    path: str = ''
    meta: dict = {}
    sid: Optional[str] = None  # browser session id for funnel linking


class NewsletterPrefsIn(BaseModel):
    subscribed: bool = True
    categories: List[str] = []


class AnnouncementIn(BaseModel):
    title: str
    body: str
    publish_at: Optional[str] = None  # ISO datetime — schedule for later


class CommunityThreadIn(BaseModel):
    title: str
    body: str


class CommunityReplyIn(BaseModel):
    body: str


class RazorpayCheckoutIn(BaseModel):
    plan: str


class RazorpayVerifyIn(BaseModel):
    order_id: str
    payment_id: Optional[str] = None
    signature: Optional[str] = None


class DigestSendIn(BaseModel):
    subject: Optional[str] = None


class AutosendIn(BaseModel):
    enabled: bool
