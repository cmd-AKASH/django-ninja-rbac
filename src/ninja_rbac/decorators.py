import inspect
import logging
from functools import wraps
from http import HTTPStatus
from typing import List

logger = logging.getLogger(__name__)

_NINJA_RBAC_DEFAULT_FORBIDDEN_MESSAGE = "You are not authorized to perform this action"
_NINJA_RBAC_PRIVILEGE_ATTRIBUTE = "permissions"


def _get_forbidden_response():
    from ninja.responses import JsonResponse

    return JsonResponse(
        data={"message": _NINJA_RBAC_DEFAULT_FORBIDDEN_MESSAGE},
        status=HTTPStatus.FORBIDDEN,
    )


def _get_privilege_requirement_text(
    privileges: List[str],
    require_all: bool,
) -> str:
    if len(privileges) == 1:
        requirement_text = f"Required privilege: {privileges[0]}"
    else:
        mode = "all" if require_all else "any"
        requirement_text = f"Required {mode} of: {privileges}"
    return requirement_text


def _has_privilege(privilege: str, user_privileges: list[str]) -> bool:
    resource, action = privilege.rsplit(sep=":", maxsplit=1)
    privilege_checks = [
        f"{resource}:{action}",
        f"{resource}:*",
    ]
    parts = resource.split(".")
    while len(parts) > 1:
        parts.pop()
        privilege_checks.append(f"{'.'.join(parts)}:*")
    privilege_checks.append("*:*")
    return any(check in user_privileges for check in privilege_checks)


def _has_privileges(
    required_privileges: List[str],
    user_privileges: List[str],
    require_all: bool = False,
) -> bool:
    privilege_check_results = [
        _has_privilege(privilege=required_privilege, user_privileges=user_privileges)
        for required_privilege in required_privileges
    ]
    # require_all = True. Checks for all privileges, while False checks if the user has at least one of the required privileges
    return all(privilege_check_results) if require_all else any(privilege_check_results)


def require_permissions(
    privileges: List[str],
    require_all: bool = False,
):
    """
    Django Ninja decorator to enforce role or privilege-based access control.

    Example usage:

    @require_permissions(['action:privilege'])

    @require_permissions([
            'buckets:create',
            'buckets:read',
            'buckets.files:read',
        ],
        require_all=False)
    """

    def decorator(view_func):
        def _check_authorization(request):
            user_privileges = (
                getattr(request.user, _NINJA_RBAC_PRIVILEGE_ATTRIBUTE, None) or []
            )

            authorized = _has_privileges(
                user_privileges=user_privileges,
                required_privileges=privileges,
                require_all=require_all,
            )

            if authorized:
                return None

            logger.warning(
                (
                    f"Access denied on {request.path}. {_get_privilege_requirement_text(privileges, require_all)}"
                )
            )

            return _get_forbidden_response()

        if inspect.iscoroutinefunction(view_func):
            # For async routes
            @wraps(view_func)
            async def async_wrapper(request, *args, **kwargs):
                response = _check_authorization(request)
                if response:
                    return response

                return await view_func(request, *args, **kwargs)

            return async_wrapper

        # For sync routes
        @wraps(view_func)
        def sync_wrapper(request, *args, **kwargs):
            response = _check_authorization(request)
            if response:
                return response

            return view_func(request, *args, **kwargs)

        return sync_wrapper

    return decorator
