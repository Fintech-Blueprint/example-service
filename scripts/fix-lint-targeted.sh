#!/bin/bash

# Fix Python line length issues
find . -name "*.py" -exec autopep8 --in-place --max-line-length 120 {} \;

# Fix YAML missing document start markers
for file in $(find . -name "*.yaml"); do
  if ! grep -q "^---" "$file"; then
    echo -e "---\n$(cat $file)" > "$file"
  fi
done

# Fix common YAML indentation issues
find . -name "*.yaml" -exec sed -i 's/^  /    /g' {} \;