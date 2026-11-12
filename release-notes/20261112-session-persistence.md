---
category: fixed
audience: users, operators
area: web-authentication
action: none
breaking: false
---
Browser sessions now survive daemon restarts: slskR persists an auto-generated JWT signing key in the state directory, restores the opt-in Remember Me option, and refreshes active local web-auth sessions automatically. OIDC sessions keep their configured JWT lifetime until provider-session revalidation is supported. Configure SLSKR_JWT_KEY or [auth.jwt] key to manage the key explicitly.
