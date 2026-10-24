# Integration procedure

Run these commands from the repository root. Use the project's full test command and build command where the examples differ. Record the snapshot and test result in the supervision log after each step.

1. Choose a tested starting commit and create one branch per integration line. Give each line one owner.

   ```sh
   SNAPSHOT=$(git rev-parse HEAD)
   git switch -c integration/a "$SNAPSHOT"
   git rev-parse HEAD
   ```

2. Check an incoming branch against the board and the shared contract. Review its changed paths and diff before merging.

   ```sh
   cat notes/board.md
   git diff --stat "$SNAPSHOT"...task/parser
   git diff --check "$SNAPSHOT"...task/parser
   git diff "$SNAPSHOT"...task/parser -- src/parser.py
   ```

3. Merge one branch and run focused tests followed by the full gate. Record the source and merge commits with the commands and result. Resolve mechanical conflicts here. Refer behavior or design conflicts to the responsible leader.

   ```sh
   git merge --no-ff task/parser
   python3 -m pytest -q tests/test_parser.py
   python3 -m pytest -q -p no:cacheprovider tests
   git log -1 --format='%h %s'
   printf 'task/parser %s | full tests passed\n' "$(git rev-parse HEAD)" >> notes/integration.log
   ```

4. Regenerate derived files from merged source. Review their diff and compare frozen default outputs and provenance hashes. Add a regression test if an approved change must alter a default.

   ```sh
   ./tools/build_site.sh
   git diff --check
   sha256sum -c tests/fixtures/default-output.sha256
   python3 -m pytest -q tests/test_provenance.py
   ```

5. Repeat steps 2 through 4 for each branch. When arrivals exceed one line's capacity, create a second line from the same snapshot. Keep its owner and merge ledger separate.

   ```sh
   git switch -c integration/b "$SNAPSHOT"
   git merge --no-ff task/cli
   python3 -m pytest -q -p no:cacheprovider tests
   ```

6. Combine related small fixes before the final merge so the final integrator handles one tested fixes branch.

   ```sh
   git switch -c integration/fixes "$SNAPSHOT"
   git merge --no-ff fix/parser
   git merge --no-ff fix/cli
   python3 -m pytest -q -p no:cacheprovider tests
   ```

7. Create the final branch from the same snapshot. Merge each tested line and the fixes branch, then absorb late branches one at a time. Regenerate derived files and run the full gate on the combined commit.

   ```sh
   git switch -c integration/final "$SNAPSHOT"
   git merge --no-ff integration/a
   git merge --no-ff integration/b
   git merge --no-ff integration/fixes
   ./tools/build_site.sh
   python3 -m pytest -q -p no:cacheprovider tests
   git rev-parse HEAD
   ```

8. Put the exact final commit and test evidence in the ledger. Verification applies to that commit. If any late merge changes it, rerun the affected checks and update the ledger.

   ```sh
   printf 'candidate %s | full tests passed\n' "$(git rev-parse HEAD)" >> notes/integration.log
   git status --short
   ```
