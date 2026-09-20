"""Tests for tenant isolation"""

import pytest
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tenant_isolation import TenantIsolator


def test_tenant_isolator_initialization():
    """Test TenantIsolator initializes correctly"""
    isolator = TenantIsolator()
    assert isolator is not None


def test_assert_validity_valid():
    """Test that valid tenant passes validation"""
    isolator = TenantIsolator()

    # Should not raise
    isolator.assert_validity({"tenant_id": "valid-tenant"})


def test_assert_validity_invalid():
    """Test that invalid tenant raises error"""
    isolator = TenantIsolator()

    # Should raise PermissionError for missing tenant_id
    with pytest.raises(PermissionError):
        isolator.assert_validity({})


def test_inject_boundary_filters():
    """Test filter injection for tenant boundaries"""
    isolator = TenantIsolator()

    filters = isolator.inject_boundary_filters({"tenant_id": "tenant-1"})

    assert filters is not None
    # Filter should contain tenant_id information
    assert "tenant" in str(filters).lower() or "tenant_id" in str(filters)


def test_tenant_isolation_multiple_tenants():
    """Test that multiple tenants are properly isolated"""
    isolator = TenantIsolator()

    tenant1_payload = {"tenant_id": "tenant-1", "data": "sensitive"}
    tenant2_payload = {"tenant_id": "tenant-2", "data": "different"}

    # Both should pass validation
    isolator.assert_validity(tenant1_payload)
    isolator.assert_validity(tenant2_payload)

    # Get filters for each
    filters1 = isolator.inject_boundary_filters(tenant1_payload)
    filters2 = isolator.inject_boundary_filters(tenant2_payload)

    # Filters should be different
    assert filters1 != filters2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
