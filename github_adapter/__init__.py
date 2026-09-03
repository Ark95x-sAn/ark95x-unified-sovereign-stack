"""ARK95X github adapter -- reports real local git state and gates pushes
through the single control plane. See github_adapter/repo_state.py.

Named `github_adapter` (not `github`) to avoid shadowing the PyPI `github`
package some of this repo's other tooling may import."""
from .repo_state import GitHubAdapter

__all__ = ["GitHubAdapter"]
