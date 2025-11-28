terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 2.15.0"
    }
  }
}

provider "docker" {}

resource "docker_network" "grid_test" {
  name = "grid_test_network"
}

resource "docker_volume" "grid_policy" {
  name = "grid_policy_volume"
}

resource "docker_container" "grid_server" {
  image = "openpolicyagent/opa:latest-envoy"
  name  = "grid-server-tf"
  networks_advanced {
    name = docker_network.grid_test.name
  }
  command = [
    "run",
    "--server",
    "--set=plugins.envoy_ext_authz_grpc.addr=:9191",
    "--set=decision_logs.console=true",
    "/policies"
  ]
  volumes {
    volume_name = docker_volume.grid_policy.name
    container_path = "/policies"
  }
}

resource "docker_container" "app" {
  image = "grid-app:latest"
  name  = "app-tf"
  networks_advanced {
    name = docker_network.grid_test.name
  }
  env = [
    "GRID_SERVER_URL=http://grid-server-tf:8181/v1/data/grid/authz/allow"
  ]
}

resource "docker_container" "test_runner" {
  image = "grid-test:latest"
  name  = "test-runner-tf"
  networks_advanced {
    name = docker_network.grid_test.name
  }
  env = [
    "APP_URL=http://app-tf:5000"
  ]
  must_run = false
  start    = true
  destroy_on_start = true
}