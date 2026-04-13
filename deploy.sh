#!/bin/bash
set -e

echo "🚀 Starting HarnessCore Deployment Script"

# 1. Cleanup old builds
echo "🧹 Cleaning up previous builds..."
rm -rf dist/ build/ *.egg-info

# 2. Build the package
echo "📦 Building HarnessCore wheel..."
uv build

# 3. Local Installation
echo "📥 Installing HarnessCore locally..."
uv pip install --force-reinstall dist/*.whl

# 4. Verification
echo "✅ Verification: Running 'uv run harness --help'"
uv run harness --help

echo ""
echo "🎉 HarnessCore has been successfully built and installed!"
echo "You can now run 'uv run harness cli \"<prompt>\"' or use the installed 'harness' command after activating your venv."
