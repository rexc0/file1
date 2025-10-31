"""Automated form filler for the KKTIX sign-up page.

This script opens the KKTIX sign-up page, generates random credentials,
and fills the registration form. It is intended for exploratory testing
purposes so that testers can quickly verify that the page accepts valid
input and that client-side validation behaves as expected.

Usage:
    python kktix_signup_tester.py [--headless] [--submit] [--screenshot PATH]

Dependencies:
    - playwright (install with ``pip install -r requirements.txt``)
    - Playwright browsers (install with ``playwright install``)
"""

import argparse
import random
import string
import sys
import time
from dataclasses import dataclass
from typing import Iterable, Optional

from playwright.sync_api import Page, Playwright, TimeoutError, sync_playwright


USERNAME_CHARSET = string.ascii_lowercase + string.digits
PASSWORD_CHARSET = string.ascii_letters + string.digits + "!@#$%^&*"


@dataclass
class FieldResult:
    """Result of a form field fill attempt."""

    label: str
    selector_used: Optional[str]
    success: bool


@dataclass
class Credentials:
    """Generated credential bundle used to populate the form."""

    username: str
    email: str
    password: str
    password_confirmation: str


def positive_int(value: str) -> int:
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("必須是正整數。")
    return number


def non_negative_float(value: str) -> float:
    number = float(value)
    if number < 0:
        raise argparse.ArgumentTypeError("必須是零或正數。")
    return number


def random_username(prefix: str, length: int) -> str:
    suffix = "".join(random.choices(USERNAME_CHARSET, k=length))
    return f"{prefix}_{suffix}"


def random_email(domain: str) -> str:
    local_part = "".join(random.choices(USERNAME_CHARSET, k=12))
    return f"{local_part}@{domain}"


def random_password(length: int) -> str:
    return "".join(random.choices(PASSWORD_CHARSET, k=length))


def fill_with_selectors(page: Page, selectors: Iterable[str], value: str) -> Optional[str]:
    for selector in selectors:
        locator = page.locator(selector)
        try:
            if locator.count() == 0:
                continue
            locator.first.fill(value)
            return selector
        except TimeoutError:
            continue
    return None


def attempt_fill(page: Page, label: str, selectors: Iterable[str], value: str) -> FieldResult:
    selector_used = fill_with_selectors(page, selectors, value)
    return FieldResult(label=label, selector_used=selector_used, success=selector_used is not None)


def click_if_exists(page: Page, selectors: Iterable[str]) -> Optional[str]:
    for selector in selectors:
        locator = page.locator(selector)
        try:
            if locator.count() == 0:
                continue
            locator.first.click()
            return selector
        except TimeoutError:
            continue
    return None


def set_checked_if_exists(page: Page, selectors: Iterable[str], checked: bool = True) -> Optional[str]:
    for selector in selectors:
        locator = page.locator(selector)
        try:
            if locator.count() == 0:
                continue
            locator.first.set_checked(checked)
            return selector
        except TimeoutError:
            continue
    return None


def generate_credentials(
    username_prefix: str,
    username_length: int,
    email_domain: str,
    password_length: int,
) -> Credentials:
    password = random_password(password_length)
    return Credentials(
        username=random_username(username_prefix, username_length),
        email=random_email(email_domain),
        password=password,
        password_confirmation=password,
    )


def run(playwright: Playwright, args: argparse.Namespace) -> list[FieldResult]:
    browser = playwright.chromium.launch(headless=args.headless, slow_mo=args.slowmo)
    context = browser.new_context()
    page = context.new_page()

    page.goto(args.url)
    page.wait_for_load_state("networkidle")

    creds = generate_credentials(
        username_prefix=args.username_prefix,
        username_length=args.username_length,
        email_domain=args.email_domain,
        password_length=args.password_length,
    )

    field_attempts: list[FieldResult] = []

    field_attempts.append(
        attempt_fill(
            page,
            label="Username",
            selectors=[
                "input[name='user[login]']",
                "input#user_login",
                "input[name*='username' i]",
                "input[name*='account' i]",
                "input[placeholder*='稱' i]",
            ],
            value=creds.username,
        )
    )

    field_attempts.append(
        attempt_fill(
            page,
            label="Email",
            selectors=[
                "input[name='user[email]']",
                "input#user_email",
                "input[type='email']",
                "input[name*='email' i]",
            ],
            value=creds.email,
        )
    )

    field_attempts.append(
        attempt_fill(
            page,
            label="Password",
            selectors=[
                "input[name='user[password]']",
                "input#user_password",
                "input[type='password']",
            ],
            value=creds.password,
        )
    )

    field_attempts.append(
        attempt_fill(
            page,
            label="Password confirmation",
            selectors=[
                "input[name='user[password_confirmation]']",
                "input#user_password_confirmation",
                "input[name*='password_confirmation' i]",
                "input[name*='confirm' i]",
            ],
            value=creds.password_confirmation,
        )
    )

    checkbox_selector = set_checked_if_exists(
        page,
        selectors=[
            "input[name='user[agree_term]']",
            "input#user_agree_term",
            "input[name*='agree' i]",
            "label:has-text('同意') input",
        ],
    )
    field_attempts.append(
        FieldResult(label="Terms checkbox", selector_used=checkbox_selector, success=checkbox_selector is not None)
    )

    if args.delay > 0:
        time.sleep(args.delay)

    if args.submit:
        submit_selector = click_if_exists(
            page,
            selectors=[
                "button[type='submit']",
                "input[type='submit']",
                "button:has-text('註冊')",
                "button:has-text('Sign Up')",
            ],
        )
        field_attempts.append(
            FieldResult(label="Submit", selector_used=submit_selector, success=submit_selector is not None)
        )
        if args.wait_after_submit > 0:
            time.sleep(args.wait_after_submit)

    if args.screenshot:
        page.screenshot(path=args.screenshot, full_page=True)

    if args.output_credentials:
        print("Generated credentials:")
        for key, value in vars(creds).items():
            print(f"  {key}: {value}")

    context.close()
    browser.close()

    return field_attempts


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fill the KKTIX sign-up form with random data.")
    parser.add_argument(
        "--url",
        default="https://kktix.com/users/sign_up",
        help="Target sign-up URL.",
    )
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode.")
    parser.add_argument(
        "--submit",
        action="store_true",
        help="Attempt to submit the form after filling the fields.",
    )
    parser.add_argument(
        "--screenshot",
        help="Save a screenshot to the provided path after filling the form.",
    )
    parser.add_argument(
        "--output-credentials",
        action="store_true",
        help="Print the randomly generated credentials to stdout.",
    )
    parser.add_argument(
        "--delay",
        type=non_negative_float,
        default=1.0,
        help="Seconds to wait after filling the form before any submission.",
    )
    parser.add_argument(
        "--wait-after-submit",
        type=non_negative_float,
        default=3.0,
        help="Seconds to wait after submitting the form.",
    )
    parser.add_argument(
        "--slowmo",
        type=non_negative_float,
        default=0,
        help="Milliseconds to slow down Playwright operations (useful for debugging).",
    )
    parser.add_argument(
        "--username-prefix",
        default="tester",
        help="Prefix for the generated username.",
    )
    parser.add_argument(
        "--username-length",
        type=positive_int,
        default=8,
        help="Random suffix length appended to the username prefix.",
    )
    parser.add_argument(
        "--email-domain",
        default="example.com",
        help="Domain used when generating an email address.",
    )
    parser.add_argument(
        "--password-length",
        type=positive_int,
        default=14,
        help="Length of the randomly generated password.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        help="Seed for Python's random module to reproduce credential values.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    if args.seed is not None:
        random.seed(args.seed)
    with sync_playwright() as playwright:
        results = run(playwright, args)

    print("\nField fill summary:")
    for result in results:
        status = "OK" if result.success else "Missing"
        selector_info = result.selector_used or "-"
        print(f"- {result.label:<24} {status:<8} selector={selector_info}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
