import Keycloak from 'keycloak-js'

const keycloak = new Keycloak({
  url: import.meta.env.VITE_KEYCLOAK_URL || `${window.location.origin}/auth`,
  realm: import.meta.env.VITE_KEYCLOAK_REALM || 'argus',
  clientId: import.meta.env.VITE_KEYCLOAK_CLIENT_ID || 'argus-frontend',
})

export default keycloak
