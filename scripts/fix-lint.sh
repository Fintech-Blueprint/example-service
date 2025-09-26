#!/bin/bash
# Fix YAML formatting and Python line length issues

# Fix YAML indentation and document start issues
find . -name "*.yaml" -exec sed -i '1i\---' {} \;
find . -name "*.yaml" -exec yamllint -f parsable {} \; | while read -r line; do
  file=$(echo "$line" | cut -d: -f1)
  if grep -q "wrong indentation" <<< "$line"; then
    # Fix indentation with yq
    yq -i 'sort_keys(..)' "$file"
  fi
done

# Fix Python line length issues
find . -name "*.py" -exec autopep8 --in-place --max-line-length 120 {} \;

# Run final lint check
echo "Running final lint check..."
yamllint . 
python -m pylint src/ tests/