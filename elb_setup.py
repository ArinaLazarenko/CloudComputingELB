import boto3
import globals as g

#IMPORTANT
# cluster1: contains t2.large instances
# cluster2: contains t2.micro instances

'''
Description: Initializes and returns clients for EC2 and Elastic Load Balancing (ELB) services using Boto3.
Outputs: 
    ec2_client (boto3.client) - The EC2 client instance.
    elb_client (boto3.client) - The ELB client instance.
'''
def initialize_clients():
    ec2_client = boto3.client('ec2')
    elb_client = boto3.client('elbv2')
    return ec2_client, elb_client

'''
Description: Reads AWS resource IDs (subnet and VPC IDs) from specified text files and returns them.
Outputs: 
    subnet_ids (list) - A list containing two subnet IDs.
    vpc_id (str) - The VPC ID read from the file.
'''
def read_aws_resource_ids():
    with open(f'{g.aws_folder_path}/subnet_id.txt', 'r') as file:
        subnet_id = file.read().strip()

    with open(f'{g.aws_folder_path}/subnet_id2.txt', 'r') as file:
        subnet_id2 = file.read().strip()
    
    with open(f'{g.aws_folder_path}/vpc_id.txt', 'r') as file:
        vpc_id = file.read().strip()
    
    return [subnet_id, subnet_id2], vpc_id

'''
Description: Filters and categorizes running EC2 instances into two lists based on their instance type: t2.micro and t2.large.
Inputs: response (dict) - The response from the describe_instances API call containing instance details.
Outputs: 
    t2_micro_instances (list) - A list of running t2.micro instance IDs.
    t2_large_instances (list) - A list of running t2.large instance IDs.
'''
def filter_running_instances(response: dict):
    t2_micro_instances = []
    t2_large_instances = []
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            if instance['State']['Name'] == 'running':
                instance_type = instance['InstanceType']
                if instance_type == 't2.micro':
                    t2_micro_instances.append(instance['InstanceId'])
                elif instance_type == 't2.large':
                    t2_large_instances.append(instance['InstanceId'])
    return t2_micro_instances, t2_large_instances


'''
Description: Finds the security group ID associated with a running EC2 instance that matches the specified security group name.
Inputs: 
    response (dict) - The response from the describe_instances API call containing instance details.
    security_group_name_to_filter (str) - The name of the security group to filter by.
Outputs: sg_id (str) - The ID of the matching security group, or an empty string if not found.
'''
def find_security_group_id(response: dict, security_group_name_to_filter: str):
    sg_id = ''
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            if instance['State']['Name'] == 'running':
                for sg in instance['SecurityGroups']:
                    if sg['GroupName'] == security_group_name_to_filter:
                        sg_id = sg['GroupId']
                        break
    return sg_id

'''
Description: Creates an internet-facing application load balancer in the specified subnets and security group.
Inputs: 
    elb_client (boto3.client) - The ELB client instance to make the request.
    subnets (list) - A list of subnet IDs where the load balancer will be created.
    sg_id (str) - The security group ID to associate with the load balancer.
Outputs: 
    load_balancer_arn (str) - The ARN of the created load balancer.
    load_balancer_dns_name (str) - The DNS name of the created load balancer.
'''
def create_load_balancer(elb_client, subnets: list, sg_id: str):
    response = elb_client.create_load_balancer(
        Name= g.load_balancer_name,
        Subnets=subnets,
        SecurityGroups=[sg_id],
        Scheme='internet-facing',
        Tags=[{'Key': 'Name', 'Value': 'load-balancer'}],
        Type='application',
        IpAddressType='ipv4'
    )
    load_balancer_arn = response['LoadBalancers'][0]['LoadBalancerArn']
    load_balancer_dns_name = response['LoadBalancers'][0]['DNSName']
    return load_balancer_arn, load_balancer_dns_name

'''
Description: Creates two target groups (for t2.micro and t2.large instances) in the specified VPC for load balancing HTTP traffic on port 8000.
Inputs: 
    elb_client (boto3.client) - The ELB client instance to make the request.
    vpc_id (str) - The VPC ID where the target groups will be created.
Outputs: 
    target_group_arn_micro (str) - The ARN of the created target group for t2.micro instances.
    target_group_arn_large (str) - The ARN of the created target group for t2.large instances.
'''
def create_target_groups(elb_client: boto3.client, vpc_id: str):
    response_micro = elb_client.create_target_group(
        Name='targets-micro',
        Protocol='HTTP',
        Port=8000,
        VpcId=vpc_id,
        HealthCheckProtocol='HTTP',
        HealthCheckPort='8000',
        HealthCheckPath='/',
        Matcher={'HttpCode': '200'},
        TargetType='instance'
    )
    target_group_arn_micro = response_micro['TargetGroups'][0]['TargetGroupArn']

    response_large = elb_client.create_target_group(
        Name='targets-large',
        Protocol='HTTP',
        Port=8000,
        VpcId=vpc_id,
        HealthCheckProtocol='HTTP',
        HealthCheckPort='8000',
        HealthCheckPath='/',
        Matcher={'HttpCode': '200'},
        TargetType='instance'
    )
    target_group_arn_large = response_large['TargetGroups'][0]['TargetGroupArn']

    return target_group_arn_micro, target_group_arn_large

'''
Description: Registers t2.micro and t2.large EC2 instances to their respective target groups.
Inputs: 
    elb_client (boto3.client) - The ELB client instance to make the request.
    target_group_arn_micro (str) - The ARN of the target group for t2.micro instances.
    target_group_arn_large (str) - The ARN of the target group for t2.large instances.
    t2_micro_instances (list) - A list of t2.micro instance IDs to register.
    t2_large_instances (list) - A list of t2.large instance IDs to register.
'''
def register_instances(elb_client: boto3.client, target_group_arn_micro: str, target_group_arn_large: str, t2_micro_instances: list, t2_large_instances: list):
    targets_micro = [{'Id': instance_id} for instance_id in t2_micro_instances]
    targets_large = [{'Id': instance_id} for instance_id in t2_large_instances]

    elb_client.register_targets(TargetGroupArn=target_group_arn_micro, Targets=targets_micro)
    elb_client.register_targets(TargetGroupArn=target_group_arn_large, Targets=targets_large)

'''
Description: Creates an HTTP listener for a load balancer and sets up routing rules to forward traffic to different target groups based on URL path patterns.
Inputs: 
    elb_client (boto3.client) - The ELB client instance to make the request.
    load_balancer_arn (str) - The ARN of the load balancer to associate the listener with.
    target_group_arn_micro (str) - The ARN of the target group for t2.micro instances.
    target_group_arn_large (str) - The ARN of the target group for t2.large instances.
'''
def create_listener_and_routes(elb_client: boto3.client, load_balancer_arn: str, target_group_arn_micro: str, target_group_arn_large: str):
    response_listener = elb_client.create_listener(
        LoadBalancerArn=load_balancer_arn,
        Protocol='HTTP',
        Port=80,
        DefaultActions=[{'Type': 'forward', 'TargetGroupArn': target_group_arn_large, 'Order': 1}]
    )
    listener_arn = response_listener['Listeners'][0]['ListenerArn']

    def register_route(listener_arn, target_group_arn, path_pattern, priority):
        elb_client.create_rule(
            ListenerArn=listener_arn,
            Conditions=[{'Field': 'path-pattern', 'Values': [path_pattern]}],
            Actions=[{'Type': 'forward', 'TargetGroupArn': target_group_arn}],
            Priority=priority
        )

    register_route(listener_arn, target_group_arn_large, '/cluster1', 1)
    register_route(listener_arn, target_group_arn_micro, '/cluster2', 2)

def main():
    # Initialize AWS clients for EC2, ELB
    ec2_client, elb_client = initialize_clients()
    
    # Read subnet and VPC IDs from files
    subnets, vpc_id = read_aws_resource_ids()
    
    # Describe EC2 instances to get their details
    response = ec2_client.describe_instances()
    
    # Get the security group name to filter from global variables
    security_group_name_to_filter = g.security_group_name

    # Filter running instances by type (t2.micro and t2.large)
    t2_micro_instances, t2_large_instances = filter_running_instances(response)
    print(f"Running t2.micro instances: {t2_micro_instances}")
    print(f"Running t2.large instances: {t2_large_instances}")

    # Find the security group ID based on the specified security group name
    sg_id = find_security_group_id(response, security_group_name_to_filter)

    if sg_id:
        print(f"Security group ID: {sg_id}")

        load_balancer_arn, load_balancer_dns_name = create_load_balancer(elb_client, subnets, sg_id)
        print(f'Load Balancer ARN: {load_balancer_arn}')
        print(f'Load Balancer DNS Name: {load_balancer_dns_name}')

        target_group_arn_micro, target_group_arn_large = create_target_groups(elb_client, vpc_id)
        print(f'Target Group ARN (t2.micro): {target_group_arn_micro}')
        print(f'Target Group ARN (t2.large): {target_group_arn_large}')

        register_instances(elb_client, target_group_arn_micro, target_group_arn_large, t2_micro_instances, t2_large_instances)
        create_listener_and_routes(elb_client, load_balancer_arn, target_group_arn_micro, target_group_arn_large)

        print('Load balancer setup complete!')
    else:
        print('No security group found with the specified name.')

if __name__ == "__main__":
    main()

    