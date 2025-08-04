# Release process

1. Commit a version bump
   - `poetry version minor` (or `patch`)
   - `poetry lock`
   - finalize `CHANGELOG.md` (must be clean as it is included in the release docs)
     - `git log 1.14.0..HEAD --pretty=format:"%s"`
2. Check CI ok
3. Tag the commit with `X.Y.Z[aW]` (e.g. `1.2.0a1`)
4. Edit & publish GH release
5. Check PyPI is ok
6. Commit a version bump
   - `poetry version preminor`
   - template for next release in `CHANGELOG.md`
   - link to annotated release notes (if any)
