# Agent Instructions

## General Guidance
- Check for existing AGENTS.md instructions before making changes. If any exist in subdirectories, apply those instructions to files in their scope.
- Maintain a clean git worktree: run `git status` to confirm only intended files are modified before committing.
- After editing files, run `scripts/check_terraform.sh` and `pytest` to ensure Terraform and Python tests pass. Install any missing dependencies as needed.
- Commit your changes locally with meaningful commit messages. You do not have permission to push to remote repositories.

## Pull Request Message
- Summarize what changed and reference relevant files using Git citations.
- Include the outcome of the test commands. If commands fail due to missing dependencies or network restrictions, note it in the testing section.
