output "instance_id" {
  description = "EC2 instance ID"
  value       = aws_instance.netmon.id
}

output "public_ip" {
  description = "Public IP of the EC2 instance"
  value       = aws_instance.netmon.public_ip
}

output "s3_bucket" {
  description = "S3 bucket for log archival"
  value       = aws_s3_bucket.logs.bucket
}

output "log_group" {
  description = "CloudWatch log group name"
  value       = aws_cloudwatch_log_group.app_logs.name
}

output "dashboard_url" {
  description = "Dashboard URL"
  value       = "http://${aws_instance.netmon.public_ip}"
}
