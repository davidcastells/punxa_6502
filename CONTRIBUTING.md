# Contributing to punxa_6502

Thank you for contributing to `punxa_6502`! To keep the repository clean and prevent merge conflicts, please follow this workflow using your GitHub fork and feature branches.

## Workflow Overview

You only need your own fork cloned locally (`origin`). Syncing with the main repository and cleaning up merged branches can be done directly from the GitHub web interface.

### 1. Start from an Up-to-Date `main` Branch

Before starting any new work, make sure your local `main` branch is up to date:

```bash
git checkout main
git pull
```

### 2. Create a Feature Branch

Create a new, descriptively named branch for each feature, fix, or experiment (for example, `feat/spi-dma` or `fix/acia-interrupt`):

```bash
git checkout -b feat/new-feature
```

### 3. Commit and Push to Your Fork

Make small, clear commits as you work, then push the branch to your fork on GitHub:

```bash
git add .
git commit -m "Describe the change clearly"
git push -u origin feat/new-feature
```

### 4. Open a Pull Request on GitHub

1. Go to your fork on GitHub (`https://github.com/<your-username>/punxa_6502`).
2. Click **Compare & pull request** (or navigate to **Pull requests > New pull request**).
3. Verify that the base repository is `davidcastells/punxa_6502` (`main`) and the compare branch is your `feat/new-feature`.
4. Add a brief description of your changes and submit the Pull Request.

### 5. After the Pull Request Is Merged

Once your Pull Request has been merged into `davidcastells/punxa_6502`, clean up your branches and sync your fork before starting new work:

1. **Delete the remote branch on GitHub:** On the merged Pull Request page, click **Delete branch** (or delete it from the **Branches** tab in your fork).
2. **Sync your fork on GitHub:** Go to your fork's main page (`https://github.com/<your-username>/punxa_6502`), click **Sync fork**, and select **Update branch**.
3. **Update your local repository and remove the local branch:**

```bash
git checkout main
git pull
git branch -d feat/new-feature
```

*(Optional: Run `git fetch --prune` occasionally to clean up stale remote branch references locally.)*

## Best Practices

* **One branch per feature:** Avoid reusing a branch for unrelated changes after its Pull Request has been merged.
* **Keep experimental work separate:** If you have rough tests or notes not ready for review, keep them on a separate branch in your fork without opening a Pull Request from it.
