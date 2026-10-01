terraform {
  required_version = ">= 1.6.0, < 2.0.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.14"
    }
  }

  # Estado local por padrão. Para time: crie um bucket com versionamento e use
  #   terraform init -backend-config=backend.hcl   (backend.hcl não versionado)
  # backend "gcs" {}
}

provider "google" {
  project               = var.project_id
  region                = var.region
  user_project_override = true
  billing_project       = var.project_id
}
