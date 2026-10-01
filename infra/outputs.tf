output "artifact_registry_repo" {
  value = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.repo.repository_id}"
}

output "ingestor_url" {
  value = google_cloud_run_v2_service.ingestor.uri
}

output "workflow" {
  value = google_workflows_workflow.batch.name
}

output "jobs" {
  value = [for j in google_cloud_run_v2_job.job : j.name]
}

output "lake_bucket" {
  value = google_storage_bucket.lake.url
}
