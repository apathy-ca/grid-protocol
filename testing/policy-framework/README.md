# GRID Policy Test Framework

This document outlines how to write and run tests for GRID policies using the Open Policy Agent (OPA) test framework. Testing policies is essential to ensure they are working correctly and to prevent regressions.

## Writing Tests

OPA tests are written in Rego, just like the policies themselves. Test files should have the `_test.rego` suffix. For example, the tests for `my-policy.rego` should be in a file named `my-policy_test.rego`.

A test is a rule that starts with `test_`. For example:

```rego
package grid.authorization

test_admin_has_full_access {
    allow with input as {
        "principal": {"role": "admin"},
        "action": {"operation": "execute"},
        "resource": {"sensitivity": "critical"}
    }
}
```

You can also assert that a rule should be false:

```rego
test_viewer_cannot_write {
    not allow with input as {
        "principal": {"role": "viewer"},
        "action": {"operation": "write"},
        "resource": {"sensitivity": "low"}
    }
}
```

## Running Tests

To run the tests, you can use the `opa test` command. You will need to provide the policy file and the test file.

```bash
opa test examples/policies/rbac-basic.rego testing/policy-framework/rbac-basic_test.rego
```

You can also run all tests in a directory:

```bash
opa test examples/policies/ testing/policy-framework/
```

A successful test run will produce output like this:

```
PASS: 2/2
```
