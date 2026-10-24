# Release verification

Start building checks before integration is complete. Run them on a named integrated commit and record commands, counts, failures, and fixes.

- **Independent computation:** Compare several separate paths against the same generated cases. Record seed, case count, and disagreements. Verify that paths do not share the same buggy helper.
- **Properties:** Test invariants, boundaries, determinism, and serialization. Keep shrinking information for failures.
- **Documentation:** Extract options, defaults, names, paths, links, and generated snippets from code and compare them with pages. Run every documented command in a controlled environment.
- **Fresh install:** Build the distribution, install into a clean environment, import it, and run a representative command. Check both wheel and source archive when applicable.
- **Publication dry run:** Inspect package and site filters, private paths, email addresses, secrets, file sizes, and generated output. Do not publish as part of the dry run.
- **Browser smoke test:** Open every route on the integrated site. Check links, console errors, controls, keyboard use, light and dark modes, and mobile width.
- **Layout:** Capture pages at desktop, tablet, and phone widths. Review contact sheets for typography, spacing, clipping, tables, code blocks, images, motion, and contrast. Rebuild and recapture after fixes.
- **Final gate:** Re-run the relevant full test suite on the final merged commit. Attach the evidence and list any remaining limitation before release approval.
