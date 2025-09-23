"""Test suite for the code generator."""
import json
import os
from pathlib import Path

import pytest

from scripts.generate_from_spec import compute_spec_sha, generate_header, write_file_atomically

ROOT = Path(__file__).resolve().parent.parent.parent

def test_compute_spec_sha():
    """Test SHA computation for feature files."""
    feature_files = list((ROOT / 'features').rglob('*.feature'))
    assert feature_files, "No feature files found"
    
    sha = compute_spec_sha(feature_files)
    assert sha and len(sha) == 64, "SHA256 should be 64 characters"

def test_generate_header():
    """Test generation of file headers."""
    spec_sha = "test_sha"
    header = generate_header(spec_sha)
    
    assert "GENERATED - do not edit" in header
    assert "generator: generate_from_spec.py" in header
    assert f"spec_sha: {spec_sha}" in header

def test_write_file_atomically(tmp_path):
    """Test atomic file writing and idempotency."""
    test_content = "test content"
    test_file = tmp_path / "test.txt"
    
    # Test initial write
    sha1 = write_file_atomically(test_file, test_content, idempotent=True)
    assert sha1
    assert test_file.read_text() == test_content
    
    # Test idempotent write with same content
    sha2 = write_file_atomically(test_file, test_content, idempotent=True)
    assert sha2 is None  # No change, no new SHA
    
    # Test write with different content
    new_content = "new content"
    sha3 = write_file_atomically(test_file, new_content, idempotent=True)
    assert sha3 and sha3 != sha1
    assert test_file.read_text() == new_content

def test_full_generation():
    """Test complete generation process."""
    # Clear previously generated files
    generated_dir = ROOT / 'generated'
    if generated_dir.exists():
        import shutil
        shutil.rmtree(generated_dir)
    
    # Run generator with signing
    exit_code = os.system(f'python {ROOT}/scripts/generate_from_spec.py --idempotent --sign')
    assert exit_code == 0, "Generator failed"
    
    # Check manifest
    manifest_file = generated_dir / 'manifest.json'
    assert manifest_file.exists(), "Manifest not generated"
    
    with open(manifest_file) as f:
        manifest = json.load(f)
    
    assert "spec_sha" in manifest
    assert "timestamp" in manifest
    assert "files" in manifest
    
    # Verify all files in manifest exist
    for filepath in manifest["files"]:
        assert Path(filepath).exists(), f"Generated file {filepath} missing"
        
    # Check spec coverage report
    coverage_file = ROOT / 'reports' / 'spec-coverage.json'
    assert coverage_file.exists(), "Coverage report not generated"
    
    with open(coverage_file) as f:
        coverage = json.load(f)
    
    assert "spec_coverage" in coverage
    assert "total_scenarios" in coverage
    assert "implemented_scenarios" in coverage
    assert "generated_files" in coverage