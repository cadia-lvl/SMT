#!/bin/bash

source environment.sh
 
LANG="$1"
EXTENSION="-uni-30"
# Train LM
function train_lm() {
  LM_DATA="$1"
  LM="$2"
  LM_ORDER="$3"
  "$MOSESDECODER"/bin/lmplz --order "$LM_ORDER" --temp_prefix "$WORK_DIR" -S 30G --discount_fallback <"$LM_DATA" >"$LM".arpa
  # we *can* use the trie structure to save about 1/2 the space, but almost twice as slow `trie`
  # we *can* use pointer compression to save more space, but slightly slower `-a 64`
  "$MOSESDECODER"/bin/build_binary -S 30G "$LM".arpa "$LM"
}

function eval_lm() {
  # LM evaluation
  LM="$1"
  TEST_SET_DIR="$2"
  for test_set in "$TEST_SET_DIR"*."$LANG"; do
    TEST_SET_NAME=$(basename "$test_set")
    echo "$TEST_SET_NAME"
    "$MOSESDECODER"/bin/query "$LM" <"$test_set" | tail -n 4
  done
}

# remove -moses
train_lm "$LM_SURFACE_TRAIN""$EXTENSION"."$LANG" "$LM_SURFACE_5""$EXTENSION"."$LANG" 5
# eval_lm "$LM_SURFACE_5"-moses."$LANG" "$LM_SURFACE_TEST"