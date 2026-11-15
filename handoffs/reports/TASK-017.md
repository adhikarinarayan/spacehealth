# TASK-017 — Complete (local setup; not deployed)

Created the root README, CITATION.cff, CI workflow and GitHub Pages workflow. No commit, push, repository creation or deployment.

## Changes

- README follows the requested order: description and disclaimer, CI badge/deploy/video placeholders, three-step setup and commands, **README science section inserted verbatim**, layout/module independence, reproducibility, direct-dependency and font licences, attribution and Apache-2.0 licence. Includes frozen/config/manifest hashes, seeds, file-verification commands, holdout reuse, DONKI and optional real-data commands, and publishing steps.
- The data inventory records the Stanford path but currently contains no download URL. README links the original Mishra paper's Data availability statement and its Stanford ZIP URL, without changing the read-only inventory or research files.
- run.py change is **module/argparse help text only**: frozen M3 plus M5 information only. AST comparison after removing the docstring is identical to HEAD.
- Vite uses `BASE_PATH`, default `/`, and rejects malformed directory paths. Example: `/spacehealth/`.
- package.json changes **scripts only**: production build also runs `test:pages`. Dependencies and lockfile unchanged.
- New built-output tests live at `.github/workflows/tests/pages.test.mjs` to respect the task fence. They check shell and local-font URLs, compiled service-worker registration/scope, exact scoped precache URLs for both cases, and cached navigation/data loading without network.
- Existing worker/precache code already resolves relative URLs against registration scope; no source change was needed to either.
- CI runs Python 3.11 and Node 26.13.1 jobs on push/PR (also manually). Dashboard builds/tests root and repository-path hosting.
- Clean-clone model tests need ignored model/out/release fixtures. `.github/workflows/prepare_model_outputs.py` verifies both committed public case manifests/file hashes before restoring their recorded model exports. It does not generate missions or rerun the holdout.
- Current real-data unit tests are synthetic and require neither the Stanford ZIP/workbook nor openpyxl. CI runs them normally and emits an explicit notice that the optional full real-data replay is skipped because its source files are not redistributed. No existing unit test requires those excluded files, so no pytest skip markers or out-of-fence test edits were needed.
- Pages uses official configure-pages/upload-pages-artifact/deploy-pages actions, with upload path dashboard/dist, main-only deployment, a github-pages environment, deployment concurrency, and pages/id-token write permissions limited to the deploy job. BASE_PATH comes from configure-pages `base_path` plus `/`, handling both root and project Pages sites.
- CITATION.cff includes software title/version/date, team and repository placeholders, licence and prototype disclaimer.

## Verification

- Full model suite: **168 passed**, exit 0.
- Scratch clean-checkout copy with papers and Stanford sources absent, generated outputs initially absent, restored via the new helper: **168 passed**, exit 0. No source downloads or holdout rerun.
- Required `npm ci`: passed after an approved network-enabled retry (sandbox DNS blocked the registry). 132 packages installed; audit reported zero vulnerabilities. npm reported an unapproved esbuild postinstall script; both builds nevertheless completed successfully without changing install-script policy or dependencies.
- Dashboard tests: **77 passed**.
- Root production build: passed, 34-file offline coverage and Pages built-output checks passed.
- `BASE_PATH=/spacehealth/ npm run build`: passed, 34-file offline coverage and Pages built-output checks passed. Final dist is this subpath build; rerun a default build before root-local production preview.
- Both workflow YAML files and CITATION.cff parsed successfully; workflow steps/permissions checked against official GitHub documentation. No live Actions run or hosted browser/offline test is claimed.
- README includes the science source bytes verbatim. LICENSE, science source, frozen configuration and canonical seed-1000 release manifest hashes remain unchanged.
- Source edits are confined to the task fence plus this requested report. DECISIONS.md also changed during the task in another session; this task did not edit it. Another session filled the README demo/video links during final verification; those edits were preserved. The source HTML comment was restored so the science insertion remains verbatim. .gitignore, root LICENSE, research, scientific logic and dashboard source/tests were not edited.

## Exact steps Narayan must perform on GitHub

1. Create an empty **public** repository under the intended account/organization. Do not upload the Stanford ZIP, PDFs, model/.venv or node_modules.
2. Review/commit the local changes yourself. Fill team/repository placeholders in CITATION.cff and replace the README CI badge placeholder. Use `main` as the default branch (or update the two main-branch references in pages.yml if choosing another name). Add the new repository as origin and push main.
3. Open **Settings → Pages → Build and deployment → Source → GitHub Actions**. Enable repository Actions if prompted. Keep the `github-pages` environment restricted to deployment from main.
4. Open **Actions → GitHub Pages → Run workflow**, select main and run it after enabling Pages. Wait for build and deploy to succeed. Later main pushes deploy automatically. No PAT is required; workflow permissions use GITHUB_TOKEN/OIDC. If the initial push ran before Pages was enabled, rerun the workflow after step 3.
5. Use the environment/deploy-job URL for `[[deploy URL]]`; fill `[[video URL]]`. Check both mission cases, then perform and record docs/OFFLINE_TEST.md against that hosted origin. Root sites use `/`; project sites use `/<repo>/` automatically.

Official references checked: https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages and https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site . Configure-pages v5 documents base_path as `/my-repo` or empty, which matches the workflow's trailing-slash handling.
