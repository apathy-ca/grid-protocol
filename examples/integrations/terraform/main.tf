provider "aws" {
  region = "us-west-2"
}

resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
}

resource "aws_ecs_cluster" "main" {
  name = "grid-cluster"
}

resource "aws_db_instance" "main" {
  allocated_storage    = 20
  engine               = "postgres"
  instance_class       = "db.t2.micro"
  name                 = "grid"
  username             = "user"
  password             = "password"
  parameter_group_name = "default.postgres13"
  skip_final_snapshot  = true
}

resource "aws_elasticache_cluster" "main" {
  cluster_id           = "grid-cache"
  engine               = "redis"
  node_type            = "cache.t2.micro"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis6.x"
  port                 = 6379
}

resource "aws_ecs_task_definition" "main" {
  family                   = "grid-gateway"
  container_definitions    = jsonencode([
    {
      name      = "grid-gateway"
      image     = "anthropics/sark:latest"
      cpu       = 256
      memory    = 512
      essential = true
      portMappings = [
        {
          containerPort = 8000
          hostPort      = 8000
        }
      ]
    }
  ])
}

resource "aws_ecs_service" "main" {
  name            = "grid-gateway"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.main.arn
  desired_count   = 3
  launch_type     = "FARGATE"

  network_configuration {
    subnets         = [aws_vpc.main.id]
    security_groups = [aws_security_group.main.id]
  }
}

resource "aws_security_group" "main" {
  name        = "grid-sg"
  description = "Allow inbound traffic to GRID gateway"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}