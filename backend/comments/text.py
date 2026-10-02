"""
Cleaning of what a commenter types: one place for the limits and the sentences shown
back to them, used by the public endpoint and by the author's reply in the admin.
"""

import re

MAX_NAME_LENGTH = 80
MAX_BODY_LENGTH = 5000

NAME_REQUIRED = "Please enter your name."
NAME_TOO_LONG = f"Names can be at most {MAX_NAME_LENGTH} characters."
EMAIL_INVALID = "Please enter a valid email address."
BODY_REQUIRED = "Please write a comment."
BODY_TOO_LONG = f"Comments can be at most {MAX_BODY_LENGTH:,} characters."
PARENT_UNAVAILABLE = "The comment you're replying to isn't available."


def clean_name(value):
    """(name, error): whitespace collapsed to single spaces, 1 to 80 characters."""
    name = " ".join(value.split())
    if not name:
        return "", NAME_REQUIRED
    if len(name) > MAX_NAME_LENGTH:
        return name, NAME_TOO_LONG
    return name, None


def clean_body(value):
    """
    (body, error): plain text with \\n line breaks, no trailing spaces on a line, at most one
    blank line in a row and nothing around it; 1 to 5,000 characters.
    """
    body = value.replace("\r\n", "\n").replace("\r", "\n")
    body = "\n".join(line.rstrip() for line in body.split("\n"))
    body = re.sub(r"\n{3,}", "\n\n", body).strip()
    if not body:
        return "", BODY_REQUIRED
    if len(body) > MAX_BODY_LENGTH:
        return body, BODY_TOO_LONG
    return body, None
