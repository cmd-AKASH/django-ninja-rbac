# django-ninja-rbac

A lightweight RBAC (Role-Based Access Control) decorator for Django Ninja APIs.

Protect your endpoints using simple privilege strings with support for wildcard permissions.

## Installation

```bash
pip install django-ninja-rbac
```

## Quick Start

Attach permissions to your authenticated user:

```python
request.user.permissions = [
    "customers:view",
    "customers:update",
]
```

Protect your Django Ninja endpoints:

```python
from ninja_rbac import require_permissions


@api.get("/customers")
@require_permissions(["customers:view"])
def get_customers(request):
    return {"success": True}
```

If the user does not have the required permission, a `403 Forbidden` response is returned:

```json
{
  "message": "You are not authorized to perform this action"
}
```

## Multiple Permissions

By default, the user must have at least one of the specified permissions.

```python
@require_permissions([
    "customers:view",
    "customers:update",
])
def endpoint(request):
    ...
```

Equivalent to:

```text
customers:view OR customers:update
```

## Require All Permissions

Set `require_all=True` to require every permission.

```python
@require_permissions(
    [
        "customers:view",
        "customers:update",
    ],
    require_all=True,
)
def endpoint(request):
    ...
```

Equivalent to:

```text
customers:view AND customers:update
```

## Wildcard Permissions

### Resource Wildcards

```python
user.permissions = [
    "customers:*"
]
```

Allows:

```text
customers:view
customers:create
customers:update
customers:delete
```

### Global Wildcard

```python
user.permissions = [
    "*:*"
]
```

Allows access to all resources and actions.

## Permission Examples

```text
customers:view
customers:create
customers:update
customers:delete

orders:view
orders:create
orders:update
orders:delete

customers:*
orders:*

*:*
```

## How It Works

Given a required permission:

```text
customers:view
```

The package checks the user's permissions in the following order:

```text
customers:view
customers:*
*:*
```

The first matching permission grants access.

## Requirements

* Python 3.11+
* Django Ninja 1.5+

## License

MIT
