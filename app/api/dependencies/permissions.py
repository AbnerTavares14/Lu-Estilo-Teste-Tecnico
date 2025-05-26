from fastapi import Depends, HTTPException, status
from typing import List

import sentry_sdk

from app.api.dependencies.auth import get_current_user 
from app.models.domain.user import UserModel 
from app.models.enum.user import UserRoleEnum 

class RoleChecker:
    def __init__(self, allowed_roles: List[UserRoleEnum]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: UserModel = Depends(get_current_user)) -> UserModel:
        user_role_value = current_user.role.value if isinstance(current_user.role, UserRoleEnum) else current_user.role
        
        allowed_role_values = [role.value for role in self.allowed_roles]

        if user_role_value not in allowed_role_values:
            sentry_sdk.capture_message(
                f"Unauthorized access attempt by {current_user.username} to role-restricted endpoint",
                level="critical"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action."
            )
        return current_user

require_admin = RoleChecker([UserRoleEnum.ADMIN])