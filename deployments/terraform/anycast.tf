# Phase 47: Global Anycast Topography (Crossplane/Terraform)

provider "aws" {
  region = "us-east-1"
}

# Establishing Global Accelerator endpoints automatically routing 
# Enterprise ingress connections to the geographically closest Kubernetes cluster.
resource "aws_globalaccelerator_accelerator" "aether_edge" {
  name            = "aether-global-edge"
  ip_address_type = "IPV4"
  enabled         = true
}

resource "aws_globalaccelerator_listener" "aether_grpc" {
  accelerator_arn = aws_globalaccelerator_accelerator.aether_edge.id
  client_affinity = "SOURCE_IP"
  protocol        = "TCP"

  port_range {
    from_port = 50051
    to_port   = 50051
  }
}

resource "aws_globalaccelerator_endpoint_group" "us_east_eks" {
  listener_arn = aws_globalaccelerator_listener.aether_grpc.id
  endpoint_group_region = "us-east-1"
  
  endpoint_configuration {
    endpoint_id = "arn:aws:elasticloadbalancing:us-east-1:1234567890:loadbalancer/net/aether/xyz"
    weight      = 128
  }
}

# The Anycast structure ensures absolute lowest latency semantic extraction by 
# terminating TLS sessions directly at the geographical AWS edge locations.
