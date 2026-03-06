# Services package
from .auth import (
    hash_password, verify_password, create_token, 
    generate_discount_code, generate_referral_code,
    get_current_user, require_user, require_admin
)
from .agents import get_agent_response
