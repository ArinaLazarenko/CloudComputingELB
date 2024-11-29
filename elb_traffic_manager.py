import boto3
import requests
import time

# Initialize boto3 clients
ec2_client = boto3.client('ec2')
elb_client = boto3.client('elbv2')

'''
Description: Retrieves the Amazon Resource Name (ARN) of a specified target group.
Inputs: target_group_name (str) - The name of the target group to retrieve the ARN for.
Outputs: target_group_arn (str) - The ARN of the specified target group.
'''
def get_target_group_arn(target_group_name: str):
    response = elb_client.describe_target_groups(Names=[target_group_name])
    return response['TargetGroups'][0]['TargetGroupArn']

import boto3

'''
Description: Retrieves the IDs of running EC2 instances of a specified instance type.
Inputs: instance_type (str) - The type of instances to filter by (e.g., 't2.micro').
Outputs: instances (list) - A list of instance IDs for the running instances of the specified type.
'''
def get_instances_from_cluster(instance_type: str):
    ec2 = boto3.client('ec2')
    
    # Use filters to get instances of a specific instance type and only running instances
    response = ec2.describe_instances(
        Filters=[
            {
                'Name': 'instance-type',
                'Values': [instance_type]
            },
            {
                'Name': 'instance-state-name',
                'Values': ['running']
            }
        ]
    )
    
    # Extract instance IDs of running instances
    instances = []
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            instances.append(instance['InstanceId'])
    
    return instances

'''
Description: Measures the response time for an EC2 instance by sending an HTTP request to port 8000.
Inputs: instance_id (str) - The ID of the EC2 instance to measure the response time for.
Outputs: response_time (float) - The time taken to receive a response in seconds, or infinity if the request fails.
'''
def measure_response_time(instance_id: str):
    print(f"Measuring response time for instance {instance_id}...")
    instance = ec2_client.describe_instances(InstanceIds=[instance_id])['Reservations'][0]['Instances'][0]
    public_ip = instance['PublicIpAddress']
    print(f"Public IP: {public_ip}")

    start_time = time.time()
    try:
        response = requests.get(f'http://{public_ip}:8000', timeout=5)
        print(f"Response: {response.text}\n")
        response_time = time.time() - start_time
        return response_time
    except requests.RequestException:
        print("Request failed\n")
        return float('inf')

'''
Description: Identifies the EC2 instance with the lowest response time from a list of instances.
Inputs: instances (list) - A list of EC2 instance IDs to evaluate.
Outputs: best_instance (str) - The ID of the instance with the lowest response time.
'''
def find_lowest_response_time_instance(instances: list):
    lowest_response_time = float('inf')
    best_instance = None

    print("\nFinding the best isntance...")
    print(f"Instances: {instances}")
    
    for instance in instances:
        response_time = measure_response_time(instance)
        if response_time < lowest_response_time:
            lowest_response_time = response_time
            best_instance = instance
    
    print(f"Best instance: {best_instance}")
    return best_instance

'''
Description: Updates an Elastic Load Balancer (ELB) target group by deregistering all instances except the specified target instance and registering it.
Inputs: 
    target_group_arn (str) - The ARN of the target group to update.
    target_instance_id (str) - The ID of the instance to register to the target group.
    instance_type (str) - The type of instances to retrieve for deregistration.
'''
def update_elb_target(target_group_arn: str, target_instance_id: str, instance_type: str):
    # Print the ARN of the target group being updated
    print(f"Updating target group with ARN: {target_group_arn}")
    print(f"Registering instance {target_instance_id} to the target group...")

    instances = get_instances_from_cluster(instance_type)
    
    # Filter out the target instance from the list of registered targets
    targets_to_deregister = [
        instance_id for instance_id in instances
        if instance_id != target_instance_id
    ]

    print(f"Targets to deregister: {targets_to_deregister}")

    # Deregister all other instances except the target instance
    if targets_to_deregister:
        elb_client.deregister_targets(
            TargetGroupArn=target_group_arn,
            Targets=[{'Id': instance_id} for instance_id in targets_to_deregister]
        )


    # Register the new target instance to the specific target group
        elb_client.register_targets(
            TargetGroupArn=target_group_arn,
            Targets=[{'Id': target_instance_id}]
        )
    
    # Confirm action
    print(f"Successfully registered instance {target_instance_id} to target group {target_group_arn}.")

# Main function
def main():
    while True:  # Infinite loop to keep running the logic
        try:
            # Get instances for each cluster
            cluster1_instances = get_instances_from_cluster('t2.large') # cluster1
            cluster2_instances = get_instances_from_cluster('t2.micro') # cluster2

            # Find the best instance for each cluster
            best_instance_cluster1 = find_lowest_response_time_instance(cluster1_instances)
            best_instance_cluster2 = find_lowest_response_time_instance(cluster2_instances)

            # Target group ARNs for each cluster
            tg_arn_cluster1 = get_target_group_arn("targets-large")
            tg_arn_cluster2 = get_target_group_arn("targets-micro")
            
            # Update the target groups with the best instance for each cluster
            update_elb_target(tg_arn_cluster1, best_instance_cluster1, "t2.large")
            update_elb_target(tg_arn_cluster2, best_instance_cluster2, "t2.micro")

            # Will find best instance every 0.1 seconds
            print("Waiting 0.1 seconds before the next update...")
            time.sleep(0.1)  # Will find best instance every 0.1 seconds

        except Exception as e:
            print(f"An error occurred: {e}")
            print("Retrying after 60 seconds...")
            time.sleep(60)  # Retry after a delay in case of an error

if __name__ == "__main__":
    main()
