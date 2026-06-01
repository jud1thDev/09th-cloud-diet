terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}


# ═══════════════════════════════════════════════════════════════
# Component 1/2 · seeded from L3-029
# ═══════════════════════════════════════════════════════════════

resource "aws_instance" "comp1_instance-t5sxze" {
  ami           = "ami-0abcdef1234567890"
  instance_type = "m5.xlarge"
  subnet_id     = aws_subnet.main.id

  root_block_device {
    volume_type           = "gp3"
    volume_size           = 20
    delete_on_termination = true
  }

  tags = {
    Name        = "instance-t5sxze"
  }
}

resource "aws_instance" "comp1_instance-kxswz6" {
  ami           = "ami-0abcdef1234567890"
  instance_type = "m5.xlarge"
  subnet_id     = aws_subnet.main.id

  root_block_device {
    volume_type           = "gp3"
    volume_size           = 20
    delete_on_termination = true
  }

  tags = {
    Name        = "instance-kxswz6"
  }
}

resource "aws_instance" "comp1_instance-eimg4q" {
  ami           = "ami-0abcdef1234567890"
  instance_type = "m5.xlarge"
  subnet_id     = aws_subnet.main.id

  root_block_device {
    volume_type           = "gp3"
    volume_size           = 20
    delete_on_termination = true
  }

  tags = {
    Name        = "instance-eimg4q"
  }
}

resource "aws_instance" "comp1_instance-yjn2ul" {
  ami           = "ami-0abcdef1234567890"
  instance_type = "m5.xlarge"
  subnet_id     = aws_subnet.main.id

  root_block_device {
    volume_type           = "gp3"
    volume_size           = 20
    delete_on_termination = true
  }

  tags = {
    Name        = "instance-yjn2ul"
  }
}

resource "aws_instance" "comp1_instance-htoyk8" {
  ami           = "ami-0abcdef1234567890"
  instance_type = "m5.xlarge"
  subnet_id     = aws_subnet.main.id

  root_block_device {
    volume_type           = "gp3"
    volume_size           = 20
    delete_on_termination = true
  }

  tags = {
    Name        = "instance-htoyk8"
  }
}

resource "aws_nat_gateway" "comp1_nat-gateway-5u2pyr" {
  allocation_id = aws_eip.comp1_nat-gateway-5u2pyr_eip.id
  subnet_id     = aws_subnet.public.id

  tags = {
    Name = "nat-gateway-5u2pyr"
  }
}

resource "aws_eip" "comp1_nat-gateway-5u2pyr_eip" {
  domain = "vpc"

  tags = {
    Name = "nat-gateway-5u2pyr-eip"
  }
}

resource "aws_instance" "comp1_instance-nhyeur" {
  ami           = "ami-0abcdef1234567890"
  instance_type = "m5.xlarge"
  subnet_id     = aws_subnet.main.id

  root_block_device {
    volume_type           = "gp3"
    volume_size           = 20
    delete_on_termination = true
  }

  tags = {
    Name        = "instance-nhyeur"
  }
}

resource "aws_instance" "comp1_instance-raisyz" {
  ami           = "ami-0abcdef1234567890"
  instance_type = "m5.xlarge"
  subnet_id     = aws_subnet.main.id

  root_block_device {
    volume_type           = "gp3"
    volume_size           = 20
    delete_on_termination = true
  }

  tags = {
    Name        = "instance-raisyz"
  }
}

resource "aws_vpc_endpoint" "comp1_vpc-endpoint-95rplc" {
  vpc_id            = aws_vpc.main.id
  service_name      = "com.amazonaws.ap-northeast-2.s3"
  vpc_endpoint_type = "Gateway"

  route_table_ids = var.private_route_table_ids

  tags = {
    Name = "vpc-endpoint-95rplc"
  }
}

# ═══════════════════════════════════════════════════════════════
# Component 2/2 · seeded from L3-025
# ═══════════════════════════════════════════════════════════════

resource "aws_nat_gateway" "comp2_nat-gateway-bpmckq" {
  allocation_id = aws_eip.comp2_nat-gateway-bpmckq_eip.id
  subnet_id     = aws_subnet.public.id

  tags = {
    Name = "nat-gateway-bpmckq"
  }
}

resource "aws_eip" "comp2_nat-gateway-bpmckq_eip" {
  domain = "vpc"

  tags = {
    Name = "nat-gateway-bpmckq-eip"
  }
}

resource "aws_subnet" "comp2_subnet-h0ehcy_1" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.0.0/20"
  availability_zone = "ap-northeast-2a"

  map_public_ip_on_launch = false

  tags = {
    Name = "subnet-h0ehcy-ap-northeast-2a"
    Type = "private"
  }
}
resource "aws_subnet" "comp2_subnet-h0ehcy_2" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.16.0/20"
  availability_zone = "ap-northeast-2b"

  map_public_ip_on_launch = false

  tags = {
    Name = "subnet-h0ehcy-ap-northeast-2b"
    Type = "private"
  }
}
resource "aws_subnet" "comp2_subnet-h0ehcy_3" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.32.0/20"
  availability_zone = "ap-northeast-2c"

  map_public_ip_on_launch = false

  tags = {
    Name = "subnet-h0ehcy-ap-northeast-2c"
    Type = "private"
  }
}

resource "aws_subnet" "comp2_subnet-w1amo1_1" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.0.0/20"
  availability_zone = "ap-northeast-2a"

  map_public_ip_on_launch = false

  tags = {
    Name = "subnet-w1amo1-ap-northeast-2a"
    Type = "private"
  }
}
resource "aws_subnet" "comp2_subnet-w1amo1_2" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.16.0/20"
  availability_zone = "ap-northeast-2b"

  map_public_ip_on_launch = false

  tags = {
    Name = "subnet-w1amo1-ap-northeast-2b"
    Type = "private"
  }
}
resource "aws_subnet" "comp2_subnet-w1amo1_3" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.32.0/20"
  availability_zone = "ap-northeast-2c"

  map_public_ip_on_launch = false

  tags = {
    Name = "subnet-w1amo1-ap-northeast-2c"
    Type = "private"
  }
}

resource "aws_subnet" "comp2_subnet-9aejsp_1" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.0.0/20"
  availability_zone = "ap-northeast-2a"

  map_public_ip_on_launch = false

  tags = {
    Name = "subnet-9aejsp-ap-northeast-2a"
    Type = "private"
  }
}
resource "aws_subnet" "comp2_subnet-9aejsp_2" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.16.0/20"
  availability_zone = "ap-northeast-2b"

  map_public_ip_on_launch = false

  tags = {
    Name = "subnet-9aejsp-ap-northeast-2b"
    Type = "private"
  }
}
resource "aws_subnet" "comp2_subnet-9aejsp_3" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.32.0/20"
  availability_zone = "ap-northeast-2c"

  map_public_ip_on_launch = false

  tags = {
    Name = "subnet-9aejsp-ap-northeast-2c"
    Type = "private"
  }
}

resource "aws_route_table" "comp2_route-table-qs9bob" {
  associated_subnets = "all_private"

  tags = {
    Name = "route-table-qs9bob"
  }
}
resource "aws_route_table" "comp2_route-table-hcty9d" {
  associated_subnets = "all_private"

  tags = {
    Name = "route-table-hcty9d"
  }
}
resource "aws_route_table" "comp2_route-table-yfaroo" {
  associated_subnets = "all_private"

  tags = {
    Name = "route-table-yfaroo"
  }
}
resource "aws_nat_gateway" "comp2_nat-gateway-qh2iyy" {
  allocation_id = aws_eip.comp2_nat-gateway-qh2iyy_eip.id
  subnet_id     = aws_subnet.public.id

  tags = {
    Name = "nat-gateway-qh2iyy"
  }
}

resource "aws_eip" "comp2_nat-gateway-qh2iyy_eip" {
  domain = "vpc"

  tags = {
    Name = "nat-gateway-qh2iyy-eip"
  }
}

resource "aws_nat_gateway" "comp2_nat-gateway-20mpgc" {
  allocation_id = aws_eip.comp2_nat-gateway-20mpgc_eip.id
  subnet_id     = aws_subnet.public.id

  tags = {
    Name = "nat-gateway-20mpgc"
  }
}

resource "aws_eip" "comp2_nat-gateway-20mpgc_eip" {
  domain = "vpc"

  tags = {
    Name = "nat-gateway-20mpgc-eip"
  }
}

resource "aws_nat_gateway" "comp2_nat-gateway-tq14jl" {
  allocation_id = aws_eip.comp2_nat-gateway-tq14jl_eip.id
  subnet_id     = aws_subnet.public.id

  tags = {
    Name = "nat-gateway-tq14jl"
  }
}

resource "aws_eip" "comp2_nat-gateway-tq14jl_eip" {
  domain = "vpc"

  tags = {
    Name = "nat-gateway-tq14jl-eip"
  }
}

resource "aws_subnet" "comp2_subnet-8wqu5m_1" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.0.0/20"
  availability_zone = "ap-northeast-2a"

  map_public_ip_on_launch = false

  tags = {
    Name = "subnet-8wqu5m-ap-northeast-2a"
    Type = "private"
  }
}
resource "aws_subnet" "comp2_subnet-8wqu5m_2" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.16.0/20"
  availability_zone = "ap-northeast-2b"

  map_public_ip_on_launch = false

  tags = {
    Name = "subnet-8wqu5m-ap-northeast-2b"
    Type = "private"
  }
}
resource "aws_subnet" "comp2_subnet-8wqu5m_3" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.32.0/20"
  availability_zone = "ap-northeast-2c"

  map_public_ip_on_launch = false

  tags = {
    Name = "subnet-8wqu5m-ap-northeast-2c"
    Type = "private"
  }
}

resource "aws_subnet" "comp2_subnet-4vjf5h_1" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.0.0/20"
  availability_zone = "ap-northeast-2a"

  map_public_ip_on_launch = false

  tags = {
    Name = "subnet-4vjf5h-ap-northeast-2a"
    Type = "private"
  }
}
resource "aws_subnet" "comp2_subnet-4vjf5h_2" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.16.0/20"
  availability_zone = "ap-northeast-2b"

  map_public_ip_on_launch = false

  tags = {
    Name = "subnet-4vjf5h-ap-northeast-2b"
    Type = "private"
  }
}
resource "aws_subnet" "comp2_subnet-4vjf5h_3" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.32.0/20"
  availability_zone = "ap-northeast-2c"

  map_public_ip_on_launch = false

  tags = {
    Name = "subnet-4vjf5h-ap-northeast-2c"
    Type = "private"
  }
}

resource "aws_subnet" "comp2_subnet-zm3doy_1" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.0.0/20"
  availability_zone = "ap-northeast-2a"

  map_public_ip_on_launch = false

  tags = {
    Name = "subnet-zm3doy-ap-northeast-2a"
    Type = "private"
  }
}
resource "aws_subnet" "comp2_subnet-zm3doy_2" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.16.0/20"
  availability_zone = "ap-northeast-2b"

  map_public_ip_on_launch = false

  tags = {
    Name = "subnet-zm3doy-ap-northeast-2b"
    Type = "private"
  }
}
resource "aws_subnet" "comp2_subnet-zm3doy_3" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.32.0/20"
  availability_zone = "ap-northeast-2c"

  map_public_ip_on_launch = false

  tags = {
    Name = "subnet-zm3doy-ap-northeast-2c"
    Type = "private"
  }
}

resource "aws_route_table" "comp2_route-table-rjyrrf" {
  associated_subnets = "same_az_private"

  tags = {
    Name = "route-table-rjyrrf"
  }
}
resource "aws_route_table" "comp2_route-table-orhdzv" {
  associated_subnets = "same_az_private"

  tags = {
    Name = "route-table-orhdzv"
  }
}
resource "aws_route_table" "comp2_route-table-9e3fqv" {
  associated_subnets = "same_az_private"

  tags = {
    Name = "route-table-9e3fqv"
  }
}