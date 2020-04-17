#!/bin/bash
# e=fail on pipeline, u=fail on unset var, x=trace commands
set -ex

# Extracts all dictionaries ending with .tsv in data/raw/dictionary and writes their contents to language separted files in data/formatted/dictionary
# Example
# extract_dicts.sh
SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
# TODO: Fix so that the knowledge of the structure is recevied from somewhere else.
SRC_DIR="$SCRIPT_DIR"/../raw/dictionary
TRG_DIR="$SCRIPT_DIR"/../formatted/dictionary

# Get all the .tsv files
for f in "$SRC_DIR"/*.tsv; do
  "$SCRIPT_DIR"/extract_dict.sh $f "$TRG_DIR"
done