# Integration procedure

Create an integration branch from a named, tested snapshot. Assign one integrator to that line. Keep a ledger of branch, source commit, merge commit, tests, and unresolved issues.

1. Review the incoming branch's diff and ownership. Check the shared contract before merging.
2. Merge one branch. Resolve mechanical conflicts; return design or behavior conflicts to a leader.
3. Run focused tests and the relevant full gate after each merge. Record the result before taking the next branch.
4. Regenerate generated code, data, and site assets from source after merges. Do not hand-merge generated output.
5. Compare default output and provenance hashes to the frozen baseline. A new config field can change hashes even when runtime behavior appears unchanged. Add a regression test for any approved default behavior.

If arrivals exceed one line's capacity, start a second integration branch from the same snapshot with a second integrator. Keep its ownership and merge order independent. Create a final branch that merges both tested lines, then absorb late work. Test the combined result. If many small fix branches target the same area, pre-merge them into one tested fixes branch and merge that once into the final line.

Do not treat a green branch test as proof of a green final branch. Record the exact integrated commit used for every verification run.
