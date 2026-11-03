# Contributing to Phone-Scanner

Thanks for helping. These steps use `master` as the main branch.

1. **Fork** the repo with the Fork button on GitHub.
2. **Clone your fork:**
   ```
   git clone https://github.com/<your-username>/PhoneScanner.git
   cd PhoneScanner
   ```
3. **Add the original repo as upstream:**
   ```
   git remote add upstream https://github.com/Antech-greyhat/PhoneScanner.git
   ```
4. **Get the latest master:**
   ```
   git checkout master
   git pull upstream master
   ```
5. **Make a branch** (use `feat/`, `fix/`, `docs/`, `test/`):
   ```
   git checkout -b fix/short-name
   ```
6. **Set up Python.**

   Windows:
   ```powershell
   py -3 -m venv .venv
   .venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-dev.txt
   ```

   Linux:
   ```bash
   python3 -m venv .venv
   .venv/bin/python -m pip install -r requirements.txt -r requirements-dev.txt
   ```
7. **Make your change.** Keep it small and about one thing.
8. **Run the checks:**
   ```
   ruff check .
   ruff format --check .
   pytest -q
   ```
9. **Commit** with a Conventional Commit message, for example
   `fix(adb): handle offline device`.
10. **Push to your fork:**
    ```
    git push -u origin fix/short-name
    ```
11. **Open a PR** on GitHub into `Antech-greyhat/PhoneScanner:master`. Fill in
    the template.
12. **Keep your fork up to date:** use the **Sync fork** button on GitHub, or
    run `git fetch upstream`, `git checkout master`, `git merge upstream/master`,
    `git push origin master`.

## Project rules

- Only test on phones you own or have permission to scan.
- Never commit real scan reports, real adb output or API keys.
- The tool must stay read-only on the phone.
- One comment style: plain `#` comments, no docstrings, no decorations.
