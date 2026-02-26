import os
from git import Repo


def main():

    REPO_NAME = "NM_lab"
    USERNAME = "awilbern52"
    TOKEN = os.getenv("GITHUB_TOKEN")

    if not TOKEN:
        raise ValueError("GITHUB_TOKEN environment variable not set")

    REMOTE_URL = f"https://{USERNAME}:{TOKEN}@github.com/{USERNAME}/{REPO_NAME}.git"

    repo = Repo.init(os.getcwd())

    if "origin" not in [r.name for r in repo.remotes]:
        repo.create_remote("origin", REMOTE_URL)
    else:
        repo.remotes.origin.set_url(REMOTE_URL)

    repo.git.add(A=True)

    if repo.is_dirty(untracked_files=True):
        repo.index.commit("update files")

    repo.git.branch("-M", "main")
    repo.git.push("-u", "origin", "main", "--force")


if __name__ == "__main__":
    main()