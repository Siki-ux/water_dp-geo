# Specification for timeIO configuration

## Environment Variables

```
DJANGO_HELMHOLTZ_CLIENT_ID=timeIO-client
DJANGO_HELMHOLTZ_CLIENT_SECRET=pUolEnz1Ve5djx9oUpw1KBgB0YgIlUOQ
DJANGO_HELMHOLTZ_AAI_CONF_URL=http://keycloak:KEYCLOAK_PORT/realms/demo/.well-known/openid-configuration

ALLOWED_VOS=UFZ-Timeseries-Management, VO
```
 __IMPORTANT NOTE FOR ORCHESTRATION:__
- `DJANGO_HELMHOLTZ_AAI_CONF_URL=http://keycloak:KEYCLOAK_PORT/realms/demo/.well-known/openid-configuration`
  - this is the internal portal of the container, so adapt to your `KEYCLOAK_PORT`
## Created groups:

  - `a:a:a:group:VO:Group1#`
  - `a:a:a:group:VO:Group2#`
  - `a:a:a:group:VO2:Group1#` (can be used as a not allowed VO)

- __Note__:

  - Please note that the `VO` name must be added to the `ALLOWED_VOS` environment variable of the `tsm-frontend` to make the group selectable

## Created user:
  - __Note__:  All users have the password `password`


| Username | Groups                                             | Purpose                                    |
| -------- | -------------------------------------------------- | ------------------------------------------ |
| `user1`  | `a:a:a:group:VO:Group1#`, `a:a:a:group:VO:Group2#` | a user in two valid groups                 |
| `user2`  | `a:a:a:group:VO:Group1#`                           | a user in one valid group, same as `user1` |
| `user3`  | `a:a:a:group:VO2:Group1#`                          | a user in a not valid virtual organization |
| `user4`  | -                                                  | a user not in any group                    |

