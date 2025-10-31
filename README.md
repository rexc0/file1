# KKTIX Sign-Up Form Random Filler

This repository contains a small Playwright-based utility that opens the
[KKTIX sign-up page](https://kktix.com/users/sign_up), generates random
credentials, and fills the registration form automatically. It can help
with exploratory testing by saving the time required to type ad-hoc data
when verifying validation behavior or testing localized UI copy.

## Prerequisites

1. Python 3.9 or newer.
2. Install dependencies and Playwright browsers:

   ```bash
   pip install -r requirements.txt
   playwright install
   ```

## Usage

```bash
python kktix_signup_tester.py --output-credentials --screenshot filled.png
```

### Helpful options

- `--headless`: run the browser without a visible window.
- `--submit`: click the submit button after filling the form. Combine with
  `--wait-after-submit` to leave the page open for a few seconds.
- `--slowmo`: slow down operations (in milliseconds) to observe each step.
- `--url`: point the tool to a different environment if needed.
- `--username-prefix`, `--username-length`: control how usernames are generated.
- `--email-domain`: choose the email domain for the random address.
- `--password-length`: increase or decrease password complexity as needed.
- `--seed`: provide a fixed seed to reproduce the same credential set.

The script prints a summary of each field it attempted to fill along with
which selector matched. This makes it easy to adjust the selector lists if
the page markup changes.
