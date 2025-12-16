#!/bin/zsh

# Sync README.md with modified image path for docs/index.md
awk '{gsub("https://github.com/nanxstats/pytest-r-snapshot/raw/main/docs/assets/logo.png", "assets/logo.png"); print}' README.md >docs/index.md

# Sync CHANGELOG.md with docs/changelog.md
cp CHANGELOG.md docs/changelog.md
