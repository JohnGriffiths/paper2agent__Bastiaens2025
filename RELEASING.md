# Release maintenance

Use GitHub tags/releases to identify the version used by collaborators. Keep the
paper skill and the MCP runtime self-contained; users may need only one component.

For each future release:

1. Review scientific source changes and retain upstream commit/license attribution.
   Changes to production tools require affected scientific comparisons and a new
   extracted-runtime installation and acceptance check.
2. Update the usage guide, limitations, validation summary, and file checksums.
   The checksum manifest covers tracked publication files except itself.
3. Create a tag and release. Attach the exact accepted MCP ZIP and its SHA-256
   file; avoid rebuilding an archive after validating its bytes.
4. Ask collaborators to record the release and exact Git commit with their results.

GitHub's automatically generated source downloads contain the full tagged
repository. The separate MCP ZIP contains only the accepted runtime subset.
GitHub may regenerate source-archive compression, so its ZIP byte hash is distinct
from the uploaded, independently tested MCP release asset. See
[GitHub source archive guarantees](https://docs.github.com/en/repositories/working-with-files/using-files/downloading-source-code-archives).

For a research DOI, a maintainer can link this public repository to Zenodo and
enable release archiving. This requires the maintainer's Zenodo/GitHub account
connection; it is not enabled by cloning the repository. See
[Zenodo's GitHub integration](https://help.zenodo.org/docs/github/enable-repository/)
and [GitHub's citation guide](https://docs.github.com/en/repositories/archiving-a-github-repository/referencing-and-citing-content).
