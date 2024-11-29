import boto3
import requests
import globals as g

# Initialize EC2 client
ec2_client = boto3.client('ec2')

# Filter by security group name
security_group_name_to_filter = g.security_group_name

# Get instances that belong to the specified security group
response = ec2_client.describe_instances()
instances = []
for reservation in response['Reservations']:
    for instance in reservation['Instances']:
        # Check if the instance belongs to the specified security group
        for sg in instance['SecurityGroups']:
            if sg['GroupName'] == security_group_name_to_filter:
                instances.append(instance)
                # print(f"Found instance {instance['InstanceId']} with public IP: {instance.get('PublicIpAddress')}")
                break  # Move to the next instance if one security group matches

'''
Description: Checks if the instance responds on port 8000 by sending an HTTP request.
Inputs: instance (dict) - AWS EC2 instance details, including the public IP.
Outputs: None (prints the health status of the instance).
'''
def check_instance_health(instance: dict):
    public_ip = instance.get('PublicIpAddress')
    if public_ip:
        url = f'http://{public_ip}:8000/'
        # print(f"Checking instance at {url}...")
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                print(f"Instance {public_ip} is up! Received response from {url}")
            else:
                print(f"Instance {public_ip} responded with status code {response.status_code}")
        except requests.ConnectionError:
            print(f"Failed to connect to {public_ip}. Server might be down.")
        except requests.Timeout:
            print(f"Request to {public_ip} timed out.")
        except requests.RequestException as e:
            print(f"An error occurred for {public_ip}: {e}")
    else:
        print(f"Instance {instance['InstanceId']} does not have a public IP.")

# Loop through all instances and call the check_instance_health function
if instances:
    print(f"Checking health of {len(instances)} instances.")
    for instance in instances:
        check_instance_health(instance)
else:
    print("No instances found in the specified security group.")
