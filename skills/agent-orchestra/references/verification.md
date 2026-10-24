# Release verification

Build the checks while feature branches are still running. Run them on a named integrated commit. The commands below show the expected shape; replace project specific tool names with the actual commands and record each command, count, failure, and fix in the verification log.

1. Freeze the candidate. Record the exact commit, clean tree state, runtime, and seed before testing.

   ```sh
   git rev-parse HEAD | tee notes/verified-commit.txt
   git status --short
   python3 --version
   ```

2. Cross check independent computation paths on generated cases. Compare a reference interpreter, compiled result, solver when applicable, derivation result, and task recomputation. Record seed, case count, and each disagreement. Confirm that the paths do not share the helper under test.

   ```sh
   python3 tools/crosscheck.py --seed 17 --cases 10000 --output notes/crosscheck.json
   python3 -m pytest -q tests/test_crosscheck.py
   ```

3. Run properties and the full test suite. Cover parser and renderer round trips, boundaries, determinism, serialization, derivation checks, and rejection of wrong answers. Keep the seed and minimized failing case.

   ```sh
   python3 -m pytest -q tests/test_properties.py
   python3 -m pytest -q -p no:cacheprovider tests
   ```

4. Compare documentation with code and run every documented command in a controlled environment. Check option names, defaults, paths, links, and generated snippets against the integrated source. Rerun notebooks if the project ships them.

   ```sh
   python3 tools/docs_check.py --check-options --check-links --run-commands
   python3 -m pytest -q tests/test_docs_examples.py
   ```

5. Build and install the actual distribution in a fresh environment. Test both wheel and source archive when applicable. Import the package and run a representative command with the clean interpreter.

   ```sh
   python3 -m build
   python3 -m venv /tmp/orchestra-verify-venv
   /tmp/orchestra-verify-venv/bin/python -m pip install dist/*.whl
   /tmp/orchestra-verify-venv/bin/python -m package_name --help
   ```

6. Perform a publication dry run without uploading. Inspect the wheel, source archive, site build, inclusion filters, file sizes, private paths, email addresses, and secrets. Review generated output as well as source files.

   ```sh
   mkdir -p /tmp/orchestra-audit/wheel /tmp/orchestra-audit/sdist
   python3 -m zipfile -e dist/*.whl /tmp/orchestra-audit/wheel
   tar -xzf dist/*.tar.gz -C /tmp/orchestra-audit/sdist
   du -sh dist site
   rg -n -i 'token|secret|password|home/|[[:alnum:]_.+-]+@[[:alnum:].-]+' /tmp/orchestra-audit site
   ```

7. Rebuild the site and review every route in a real browser. Check console errors, links, controls, keyboard operation, light and dark modes, and a narrow viewport. If previews share one port, reattach them after the build.

   ```sh
   ORCH_BUILD_CMD=./tools/build_site.sh ORCH_PREVIEWS_FILE=notes/previews.tsv skills/agent-orchestra/scripts/rebuild_with_previews.sh
   python3 -m http.server 8765 --directory site
   ```

8. Capture desktop, tablet, and phone views. Review contact sheets for typography, spacing, clipping, tables, code blocks, images, motion, and contrast. Fix issues, rebuild, and capture again. Avoid scrolling during headless capture.

   ```sh
   skills/agent-orchestra/scripts/shot.sh http://localhost:8765/ notes/shots/home-desktop.png 1440 3200
   skills/agent-orchestra/scripts/shot.sh http://localhost:8765/ notes/shots/home-tablet.png 820 3200
   skills/agent-orchestra/scripts/shot.sh http://localhost:8765/ notes/shots/home-phone.png 390 3200
   python3 skills/agent-orchestra/scripts/contact_sheet.py notes/shots/home-sheet.png notes/shots/home-*.png
   ```

9. Run the full gate on the final merged commit. Save the commit, commands, counts, screenshots, and remaining limitations. If the commit changed since step 1, repeat affected checks before release approval.

   ```sh
   python3 -m pytest -q -p no:cacheprovider tests
   test "$(git rev-parse HEAD)" = "$(cat notes/verified-commit.txt)"
   git status --short
   ```
