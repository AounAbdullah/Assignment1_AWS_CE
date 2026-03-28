import boto3
import botocore.exceptions

ec2_client = boto3.client('ec2')


ec2_client.run_instances(
    "max_count": 1,
    "min_count": 1,
    "image_id": "ami-02dfbd4ff395f2a1b",
    "instance_type": "t3.micro",
    "key_name": "unievents-key",
    "ebs_optimized": true,
    "network_interfaces": [{"subnet_id": "subnet-0df026a6b6e1718a2", "associate_public_ip_address": false, "device_index": 0, "groups": ["sg-0a57dad8dc33cf80f"]}],
    "credit_specification": {"cpu_credits": "unlimited"},
    "tag_specifications": [{"resource_type": "instance", "tags": [{"key": "Name", "value": "unievents-ec2-2"}]}],
    "iam_instance_profile": {"arn": "arn:aws:iam::166818437703:instance-profile/unieventss3"},
    "metadata_options": {"http_endpoint": "enabled", "http_put_response_hop_limit": 2, "http_tokens": "required"},
    "private_dns_name_options": {"hostname_type": "ip-name", "enable_resource_name_dns_arecord": false, "enable_resource_name_dns_aaaarecord": false}
)
