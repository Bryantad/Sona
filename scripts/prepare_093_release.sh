#!/usr/bin/env bash
set -euo pipefail

PREV_TAG="${1:-v0.9.2}"
APPLY_CHANGES=0

# Check for apply flag
if [[ "${2:-}" == "--apply" ]]; then
  APPLY_CHANGES=1
fi

# Collect added/modified since previous tag
mapfile -t CHANGED < <(git diff --name-status "$PREV_TAG"..HEAD | awk '/^(A|M)\s/ {print $2}')

echo "=== Sona v0.9.3 Release Staging Plan ==="
echo "Analyzing changes since ${PREV_TAG}..."

allow=(
  "src/**" "sona/**"
  "pyproject.toml" "setup.cfg" "ruff.toml" "tox.ini"
  "vscode-extension/**"
  "security/**" ".sona-policy.json"
  "README.md" "CHANGELOG.md" "FEATURE_FLAGS.md" "RESEARCH_AUDIT.md" "SECURITY.md" "docs/**"
  "tests/**"
  "scripts/**" ".github/**"
)

deny=(
  ".venv/**" "venv/**" ".mypy_cache/**" ".pytest_cache/**" "dist/**" "build/**" "*.egg-info/**"
  "*.log" "*.jsonl" "*.tmp" "*.bak" "*.swp" "*.ipynb" "nohup.out"
  ".idea/**" ".vscode/**" "*.code-workspace"
  "coverage/**" "htmlcov/**" ".coverage*"
  "data/**" "datasets/**" "local/**" "experiments/**" "playground/**" "scratch/**" "notes/**"
  "*.bin" "*.pt" "*.safetensors" "*.zip" "*.tar*" "*.7z"
)

match_glob() { # path, patterns...
  local p="$1"; shift
  for g in "$@"; do
    [[ "$p" == $g ]] && return 0
  done
  return 1
}

# Filter files
keep=()
for f in "${CHANGED[@]}"; do
  match_glob "$f" "${allow[@]}" || continue
  match_glob "$f" "${deny[@]}" && continue
  keep+=("$f")
done

# Categorize files
declare -A categories
categories["Core/CLI"]=()
categories["VS Code"]=()
categories["Policies/Security"]=()
categories["Docs"]=()
categories["Tests"]=()
categories["Scripts/CI"]=()
categories["Other"]=()

for f in "${keep[@]}"; do
  if [[ "$f" =~ ^src/ ]] || [[ "$f" =~ ^sona/ ]] || [[ "$f" =~ pyproject\.toml ]] || 
     [[ "$f" =~ setup\.cfg ]] || [[ "$f" =~ ruff\.toml ]] || [[ "$f" =~ tox\.ini ]]; then
    categories["Core/CLI"]+=("$f")
  elif [[ "$f" =~ ^vscode-extension/ ]]; then
    categories["VS Code"]+=("$f")
  elif [[ "$f" =~ ^security/ ]] || [[ "$f" =~ \.sona-policy\.json ]]; then
    categories["Policies/Security"]+=("$f")
  elif [[ "$f" =~ README\.md ]] || [[ "$f" =~ CHANGELOG\.md ]] || [[ "$f" =~ FEATURE_FLAGS\.md ]] || 
       [[ "$f" =~ RESEARCH_AUDIT\.md ]] || [[ "$f" =~ SECURITY\.md ]] || [[ "$f" =~ ^docs/ ]]; then
    categories["Docs"]+=("$f")
  elif [[ "$f" =~ ^tests/ ]]; then
    categories["Tests"]+=("$f")
  elif [[ "$f" =~ ^scripts/ ]] || [[ "$f" =~ ^\.github/ ]]; then
    categories["Scripts/CI"]+=("$f")
  else
    categories["Other"]+=("$f")
  fi
done

# Print categorized results
echo -e "\nFiles to stage by category (${#keep[@]} total):\n"

for category in "${!categories[@]}"; do
  files=("${categories[$category][@]}")
  if [ ${#files[@]} -gt 0 ]; then
    echo -e "\033[1;33m$category (${#files[@]} files):\033[0m"
    for f in "${files[@]}"; do
      echo "  - $f"
    done
    echo ""
  fi
done

# Generate git add commands
echo -e "\033[1;36m=== Git Add Commands ===\033[0m"
echo -e "\033[0;32m# Run these commands to stage the release:\033[0m"
for f in "${keep[@]}"; do
  echo "git add -- \"$f\""
done

# Generate commit message
echo -e "\n\033[1;36m=== Draft Commit Message ===\033[0m"
cat << 'EOT'
release: v0.9.3 (infra, flags, policy, diagnostics)

- CLI: Added doctor, build-info, and ai-* command stubs
- Infrastructure: Implemented policy engine and circuit breaker pattern
- Configuration: Added feature flag system for staged rollout
- VS Code: Added Focus Mode toggle with ADHD/dyslexia profile stubs
- Documentation: Updated for v0.9.3 features and infrastructure

Refs: #release-0.9.3
EOT

# Tag command
echo -e "\n\033[1;36m=== Tag Command ===\033[0m"
echo 'git tag -a v0.9.3 -m "Sona v0.9.3"'

echo -e "\n\033[1;35mInstructions:\033[0m"
echo "1. Review the files to be staged"
echo "2. Run the git add commands (or run this script with --apply)"
echo "3. Run sanity checks: pytest -q, ruff check ."
echo "4. Verify staged files: git diff --cached --name-status" 
echo "5. Commit and tag when ready"

# Apply changes if requested
if [ $APPLY_CHANGES -eq 1 ]; then
  echo -e "\n\033[1;33mApplying changes...\033[0m"
  for f in "${keep[@]}"; do
    git add -- "$f"
  done
  
  echo -e "\n\033[0;32mStaged set:\033[0m"
  git diff --cached --name-status
fi
