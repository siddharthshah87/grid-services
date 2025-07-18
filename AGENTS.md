# Agent Instructions

## General Guidance
- Check for existing AGENTS.md instructions before making changes. If any exist in subdirectories, apply those instructions to files in their scope.
- Maintain a clean git worktree: run `git status` to confirm only intended files are modified before committing.
- After editing files, run `scripts/check_terraform.sh` and `pytest` to ensure Terraform and Python tests pass. Install any missing dependencies as needed.
- Do **not** run Terraform commands such as `terraform init`, `terraform plan`, `terraform apply`, or `terraform destroy`.
- Do **not** attempt to push Docker images or run scripts that modify cloud resources (e.g., `dev_up.sh`, `dev_down.sh`, `bootstrap_state.sh`, `fix_and_apply.sh`).
- Commit your changes locally with meaningful commit messages. You do not have permission to push to remote repositories.

## Pull Request Message
- Summarize what changed and reference relevant files using Git citations.
- Include the outcome of the test commands. If commands fail due to missing dependencies or network restrictions, note it in the testing section.
