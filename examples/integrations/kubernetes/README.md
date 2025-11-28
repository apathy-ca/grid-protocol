# GRID Kubernetes Integration Examples

This directory contains examples of how to deploy and configure GRID in a Kubernetes environment.

## Examples

- **[deployment.yaml](deployment.yaml):** A sample Kubernetes deployment for a GRID gateway (e.g., SARK).
- **[network-policy.yaml](network-policy.yaml):** A network policy that forces all traffic through the GRID gateway, preventing shadow IT.

## Deployment

To deploy these examples to your Kubernetes cluster:

```bash
# Apply the deployment
kubectl apply -f examples/integrations/kubernetes/deployment.yaml

# Apply the network policy
kubectl apply -f examples/integrations/kubernetes/network-policy.yaml
```

## Configuration

### Deployment

The `deployment.yaml` file includes a sample configuration for a GRID gateway. You will need to customize this configuration for your environment, including:

- **Authentication:** Configure your authentication provider (e.g., OIDC, LDAP, SAML).
- **Database:** Configure your database connection.
- **Policy Engine:** Configure your policy engine (e.g., OPA).

### Network Policy

The `network-policy.yaml` file is designed to force all traffic through the GRID gateway. You may need to customize this policy for your specific network topology and security requirements.

## Shadow IT Prevention

The `network-policy.yaml` file is a critical component of a defense-in-depth strategy to prevent shadow IT. By blocking all direct service-to-service communication, it ensures that all traffic is subject to GRID governance.

For more information on shadow IT, see the [GRID Shadow IT and Governance Gaps](../../GRID_SHADOW_IT_AND_GOVERNANCE_GAPS.md) document.