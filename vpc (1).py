import boto3
import botocore.exceptions

ec2_client = boto3.client('ec2')


ec2_client.create_vpc(
    "cidr_block": "10.0.0.0/16",
    "amazon_provided_ipv6cidr_block": false,
    "instance_tenancy": "default",
    "tag_specifications": [{"resource_type": "vpc", "tags": [{"key": "Name", "value": "unievents-vpc"}]}]
)


ec2_client.modify_vpc_attribute(
    "vpc_id": "preview-vpc-1234",
    "enable_dns_hostnames": {"value": true}
)


ec2_client.describe_vpcs(
    "vpc_ids": ["preview-vpc-1234"]
)


ec2_client.create_subnet(
    "vpc_id": "preview-vpc-1234",
    "cidr_block": "10.0.144.0/20",
    "availability_zone": "us-east-1b",
    "ipv6cidr_block": undefined,
    "tag_specifications": [{"resource_type": "subnet", "tags": [{"key": "Name", "value": "unievents-subnet-private2-us-east-1b"}]}]
)


ec2_client.create_internet_gateway(
    "tag_specifications": [{"resource_type": "internet-gateway", "tags": [{"key": "Name", "value": "unievents-igw"}]}]
)


ec2_client.attach_internet_gateway(
    "internet_gateway_id": "preview-igw-1234",
    "vpc_id": "preview-vpc-1234"
)


ec2_client.create_route_table(
    "vpc_id": "preview-vpc-1234",
    "tag_specifications": [{"resource_type": "route-table", "tags": [{"key": "Name", "value": "unievents-rtb-private2-us-east-1b"}]}]
)


ec2_client.create_route(
    "route_table_id": "preview-rtb-private-2",
    "destination_cidr_block": "0.0.0.0/0",
    "nat_gateway_id": "preview-nat-0"
)


ec2_client.associate_route_table(
    "route_table_id": "preview-rtb-private-2",
    "subnet_id": "preview-subnet-private-3"
)


ec2_client.allocate_address(
    "domain": "vpc",
    "tag_specifications": [{"resource_type": "elastic-ip", "tags": [{"key": "Name", "value": "unievents-eip-us-east-1a"}]}]
)


ec2_client.create_nat_gateway(
    "subnet_id": "preview-subnet-public-0",
    "allocation_id": "preview-eipalloc-0",
    "tag_specifications": [{"resource_type": "natgateway", "tags": [{"key": "Name", "value": "unievents-nat-public1-us-east-1a"}]}]
)


ec2_client.describe_nat_gateways(
    "nat_gateway_ids": ["preview-nat-0"],
    "filter": [{"name": "state", "values": ["available"]}]
)


ec2_client.describe_route_tables(
    "route_table_ids": [undefined, undefined, "preview-rtb-private-1", "preview-rtb-private-2"]
)
