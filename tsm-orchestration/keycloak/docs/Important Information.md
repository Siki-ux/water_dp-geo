# Important Information

With important information we mean theses kind of information you'll need to connect you application with the client to keycloak.

- Make sure you have selected the right realm `demo`
- The Client ID
  - Go to `clients` in left menu
  - Select the client you want, e.g. `timeIO-client`
  - there you find the `Client ID`
- The Client Secret
  - Go to `clients` in left menu
  - Select the client you want, e.g. `timeIO-client`
  - go to `Credentials` tab
  - there you find the `Client Secret`
- Well Known Url
  - Go to `realm settings` in left menu
  - in the current `general` tab you find the `Endpoints`
  - Select the `OpenID Endpoint Configuration`
  - e.g. `http://keycloak:KEYCLOAK_PORT/realms/demo/.well-known/openid-configuration`
