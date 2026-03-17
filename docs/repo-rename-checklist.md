# Repo Rename Checklist: old repo name -> `shelf`

This checklist is for the moment when the GitHub repository is actually renamed to `shelf`.

Do not switch every hard-coded URL before the GitHub rename is real, or some public links will break temporarily.

## Rename on GitHub first

- rename the repository on GitHub from `framework` to `shelf`
- verify that the new canonical URL is `https://github.com/xueyu888/shelf`

## Update local git remote

Run this after the GitHub rename:

```bash
git remote set-url origin https://github.com/xueyu888/shelf.git
git remote -v
```

## Update public-facing links in the repo

After the rename, switch remaining hard-coded URLs that still point to the old repository path.

Main places to update:

- `README.md`
- `tools/vscode/shelf-ai/package.json`
- `.github/ISSUE_TEMPLATE/config.yml`
- release notes or launch posts that still mention the old repo path

## Update social and launch assets

- re-export `docs/github-social-preview.png` if you want the visible repo URL to match the new repo exactly
- update any post drafts that still mention the old repository URL

## Check GitHub repository settings

- About URL and description
- Topics
- Social Preview image
- Discussions setting
- Releases page

## Verify redirects and badges

- open the old repo URL and confirm GitHub redirects cleanly
- confirm README badges resolve correctly
- confirm release links still work
- confirm issue template contact links still work

## Shelf AI metadata

If you publish the extension again after the rename, update:

- `repository.url`
- `bugs.url`
- `homepage`

in `tools/vscode/shelf-ai/package.json`

## Final sanity check

Run:

```bash
git remote -v
rg -n "<old-owner>/<old-repo>" README.md CONTRIBUTING.md docs .github tools/vscode/shelf-ai -g '!docs/examples/**'
```

The remaining hits should be intentional historical references only.
