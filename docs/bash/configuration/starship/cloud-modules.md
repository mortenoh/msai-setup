# Cloud Modules

Starship can display cloud provider contexts, helping you track which environment you're working with. This is essential for avoiding accidental operations in production or the wrong cluster.

## Overview

| Module | Purpose | Detection |
|--------|---------|-----------|
| `aws` | AWS profile and region | `~/.aws/`, `$AWS_*` vars |
| `gcloud` | Google Cloud project | `gcloud config` |
| `azure` | Azure subscription | `~/.azure/` |
| `kubernetes` | K8s context and namespace | `~/.kube/config` |
| `docker_context` | Docker context | `docker context` |
| `terraform` | Terraform workspace | `.terraform/` |
| `pulumi` | Pulumi stack | `Pulumi.yaml` |
| `vagrant` | Vagrant environment | `Vagrantfile` |

## AWS

Shows the active AWS profile and region.

### Configuration

```toml
[aws]
format = 'on [$symbol($profile )(\($region\) )(\[$duration\] )]($style)'
symbol = " "
style = "bold yellow"
disabled = false
expiration_symbol = "X"
force_display = false
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `symbol` | ` ` | AWS symbol |
| `style` | `bold yellow` | Text style |
| `expiration_symbol` | `X` | Shown when credentials expire |
| `force_display` | false | Show even without credentials |

### Region Aliases

Map long region names to short aliases:

```toml
[aws.region_aliases]
us-east-1 = "ue1"
us-west-2 = "uw2"
eu-west-1 = "ew1"
eu-central-1 = "ec1"
ap-southeast-1 = "as1"
ap-northeast-1 = "an1"
```

### Profile Aliases

Shorten profile names:

```toml
[aws.profile_aliases]
CompanyProductionAccount = "prod"
CompanyStagingAccount = "stage"
CompanyDevelopmentAccount = "dev"
```

### Examples

**Show profile and region:**

```toml
[aws]
format = '[$symbol$profile($region)]($style) '
symbol = "aws "
```

Output: `aws prod(ue1) `

**Highlight production profiles:**

```toml
[aws]
format = '[$symbol$profile($region)]($style) '

[aws.profile_aliases]
production = "[PROD]"

# Use conditional styling through format
```

**Minimal display:**

```toml
[aws]
format = '[$profile]($style) '
symbol = ""
```

### Session Duration

Show credential expiration for temporary credentials:

```toml
[aws]
format = '[$symbol$profile(\[$duration\])]($style) '
```

Shows remaining time for AWS SSO or assumed role sessions.

## Google Cloud

Shows the active GCP project and configuration.

### Configuration

```toml
[gcloud]
format = 'on [$symbol$account(@$domain)(\($region\))]($style) '
symbol = " "
style = "bold blue"
disabled = false
detect_env_vars = []
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `symbol` | ` ` | GCP symbol |
| `style` | `bold blue` | Text style |
| `detect_env_vars` | `[]` | Additional env vars to detect |

### Region Aliases

```toml
[gcloud.region_aliases]
us-central1 = "uc1"
europe-west1 = "ew1"
asia-east1 = "ae1"
```

### Project Aliases

```toml
[gcloud.project_aliases]
very-long-project-name = "short"
my-company-production = "prod"
```

### Examples

**Show project only:**

```toml
[gcloud]
format = '[$symbol$project]($style) '
```

**Show account and region:**

```toml
[gcloud]
format = '[$symbol$account(@$domain)($region)]($style) '
```

## Azure

Shows the active Azure subscription.

### Configuration

```toml
[azure]
format = "on [$symbol($subscription)]($style) "
symbol = " "
style = "bold blue"
disabled = true  # Disabled by default
```

### Examples

**Enable Azure module:**

```toml
[azure]
disabled = false
format = '[$symbol$subscription]($style) '
```

**With subscription aliases:**

```toml
[azure]
disabled = false
format = '[$symbol$subscription]($style) '

[azure.subscription_aliases]
"Visual Studio Enterprise" = "VSE"
"Production Subscription" = "PROD"
```

## Kubernetes

Shows the current Kubernetes context and namespace.

### Configuration

```toml
[kubernetes]
format = '[$symbol$context( \($namespace\))]($style) '
symbol = " "
style = "bold cyan"
disabled = true  # Disabled by default
detect_env_vars = []
detect_extensions = []
detect_files = []
detect_folders = []
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `symbol` | ` ` | K8s symbol |
| `style` | `bold cyan` | Text style |
| `disabled` | true | Disabled by default |
| `detect_*` | `[]` | File-based detection |

### Context Aliases

Map cluster names to readable aliases:

```toml
[kubernetes.context_aliases]
"arn:aws:eks:us-east-1:123456789:cluster/production" = "prod"
"arn:aws:eks:us-east-1:123456789:cluster/staging" = "stage"
"gke_mycompany_us-central1_production" = "gke-prod"
"docker-desktop" = "docker"
"minikube" = "mini"
```

### User Aliases

Map user names:

```toml
[kubernetes.user_aliases]
"arn:aws:eks:us-east-1:123456789:cluster/production" = "eks-prod"
```

### Examples

**Enable Kubernetes:**

```toml
[kubernetes]
disabled = false
format = '[$symbol$context:$namespace]($style) '
```

**Show only in specific directories:**

```toml
[kubernetes]
disabled = false
detect_files = ["k8s", "kubernetes", "helm"]
detect_folders = ["charts", "manifests"]
```

**Context and namespace with aliases:**

```toml
[kubernetes]
disabled = false
format = '[$symbol$context($namespace)]($style) '

[kubernetes.context_aliases]
"arn:aws:eks:us-east-1:123456789:cluster/production" = "PROD"
"arn:aws:eks:us-east-1:123456789:cluster/staging" = "STAGE"
```

Output: `PROD(backend) `

**Highlight production contexts:**

```toml
[kubernetes]
disabled = false
format = '[$symbol$context($namespace)]($style) '
style = "cyan"

[kubernetes.context_aliases]
"production-cluster" = "PROD"
```

## Docker Context

Shows the active Docker context.

### Configuration

```toml
[docker_context]
format = "via [$symbol$context]($style) "
symbol = " "
style = "blue bold"
disabled = false
only_with_files = true
detect_extensions = []
detect_files = ["docker-compose.yml", "docker-compose.yaml", "Dockerfile"]
detect_folders = []
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `only_with_files` | true | Only show with Docker files |
| `detect_files` | Dockerfile, compose | Files to detect |

### Examples

**Always show Docker context:**

```toml
[docker_context]
only_with_files = false
format = '[$symbol$context]($style) '
```

**Show only when not default:**

```toml
[docker_context]
format = '[$symbol$context]($style) '
# Will automatically hide when context is "default"
```

## Terraform

Shows the active Terraform workspace.

### Configuration

```toml
[terraform]
format = "via [$symbol$workspace]($style) "
symbol = " "
style = "bold 105"
disabled = false
detect_extensions = ["tf", "tfplan", "tfstate"]
detect_files = []
detect_folders = [".terraform"]
```

### Examples

**Enable Terraform:**

```toml
[terraform]
format = '[$symbol$workspace]($style) '
symbol = "tf "
```

Output: `tf production `

**Custom workspace display:**

```toml
[terraform]
format = '[$symbol$version $workspace]($style) '
```

## Pulumi

Shows the active Pulumi stack.

### Configuration

```toml
[pulumi]
format = "via [$symbol($username@)$stack]($style) "
symbol = " "
style = "bold 5"
disabled = false
search_upwards = true
```

### Examples

**Enable Pulumi:**

```toml
[pulumi]
format = '[$symbol$stack]($style) '
```

## Complete Cloud Configuration

A comprehensive setup for multi-cloud environments:

```toml
format = """
$directory\
$git_branch\
$git_status\
$aws\
$gcloud\
$azure\
$kubernetes\
$docker_context\
$terraform\
$line_break\
$character"""

# AWS
[aws]
format = '[$symbol$profile(\($region\))]($style) '
symbol = "aws:"
style = "bold yellow"

[aws.region_aliases]
us-east-1 = "ue1"
us-west-2 = "uw2"
eu-west-1 = "ew1"

[aws.profile_aliases]
production = "PROD"
staging = "STAGE"

# Google Cloud
[gcloud]
format = '[$symbol$project(\($region\))]($style) '
symbol = "gcp:"
style = "bold blue"

[gcloud.region_aliases]
us-central1 = "usc1"
europe-west1 = "euw1"

# Azure
[azure]
disabled = false
format = '[$symbol$subscription]($style) '
symbol = "az:"
style = "bold cyan"

# Kubernetes
[kubernetes]
disabled = false
format = '[$symbol$context(:$namespace)]($style) '
symbol = "k8s:"
style = "bold green"

[kubernetes.context_aliases]
"arn:aws:eks:us-east-1:123456789:cluster/prod" = "eks-prod"
"gke_company_us-central1_production" = "gke-prod"
"docker-desktop" = "local"

# Docker
[docker_context]
format = '[$symbol$context]($style) '
symbol = "docker:"
only_with_files = true

# Terraform
[terraform]
format = '[$symbol$workspace]($style) '
symbol = "tf:"
```

## Safety Considerations

Cloud context modules help prevent mistakes like running production commands in the wrong environment:

1. **Use distinct aliases** - Make production contexts stand out
2. **Enable relevant modules** - Keep cloud context visible
3. **Use color coding** - Consider red/yellow for production

```toml
# Example: Make production prominent
[kubernetes.context_aliases]
"production-cluster" = "[PRODUCTION]"
"staging-cluster" = "staging"
"development-cluster" = "dev"
```
