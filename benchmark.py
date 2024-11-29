import asyncio
import aiohttp
import time
import boto3
import globals as g
from datetime import datetime, timedelta


# Get instance health checks for a given target group
def get_instance_health(elb_client, target_group_arn):
    try:
        response = elb_client.describe_target_health(TargetGroupArn=target_group_arn)
        return response['TargetHealthDescriptions']
    except Exception as e:
        print(f"Error fetching instance health: {str(e)}")
        return None


# Get CPU utilization from CloudWatch for a given instance
def get_cpu_utilization(cloudwatch_client, instance_id):
    try:
        response = cloudwatch_client.get_metric_statistics(
            Namespace='AWS/EC2',
            MetricName='CPUUtilization',
            Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
            StartTime=datetime.utcnow() - timedelta(minutes=10),
            EndTime=datetime.utcnow(),
            Period=300,
            Statistics=['Average'],
        )
        datapoints = response.get('Datapoints', [])
        if datapoints:
            return datapoints[-1]['Average']  # Return the latest data point
        return None
    except Exception as e:
        print(f"Error fetching CPU utilization for instance {instance_id}: {str(e)}")
        return None


async def call_endpoint_http(session, request_num, endpoint, dns_name):
    url = f"http://{dns_name}{endpoint}"
    headers = {'content-type': 'application/json'}
    try:
        async with session.get(url, headers=headers) as response:
            status_code = response.status
            response_json = await response.json()
            print(f"Request {request_num} to {endpoint}: Response: {response_json}")
            return status_code, response_json
    except Exception as e:
        print(f"Request {request_num} to {endpoint}: Failed - {str(e)}")
        return None, str(e)


def get_target_group_arn(target_group_name):
    """
    Retrieves the ARN of the target group by its name.

    :param target_group_name: The name of the target group
    :return: The ARN of the target group
    """
    # Initialize a Boto3 client for the Elastic Load Balancing service
    client = boto3.client('elbv2')

    # Describe the target group by name
    response = client.describe_target_groups(Names=[target_group_name])

    # Extract the target group ARN from the response
    target_group_arn = response['TargetGroups'][0]['TargetGroupArn']
    
    return target_group_arn


async def main():
    num_requests = 1000

    # Initialize the ELB and CloudWatch clients
    elb_client = boto3.client('elbv2')
    cloudwatch_client = boto3.client('cloudwatch')

    # Describe the load balancer
    response = elb_client.describe_load_balancers(
        Names=[g.load_balancer_name]
    )

    # Extract the DNS name for the specific load balancer
    load_balancer = response['LoadBalancers'][0]
    dns_name = load_balancer['DNSName']

    # Define the ARNs for the target groups of cluster1 and cluster2
    target_group_arn_cluster1 = get_target_group_arn(g.targer_group_large_name)
    target_group_arn_cluster2 = get_target_group_arn(g.targer_group_micro_name)

    # Get instance health and CPU utilization for cluster1
    print("\n--- Cluster1 (Target Group 1) ---")
    instance_health_cluster1 = get_instance_health(elb_client, target_group_arn_cluster1)
    if instance_health_cluster1:
        for target in instance_health_cluster1:
            instance_id = target['Target']['Id']
            health_status = target['TargetHealth']['State']
            print(f"Instance {instance_id} health: {health_status}")

            # Get CPU utilization
            cpu_utilization = get_cpu_utilization(cloudwatch_client, instance_id)
            if cpu_utilization is not None:
                print(f"Instance {instance_id} CPU utilization: {cpu_utilization:.2f}%")
            else:
                print(f"CPU utilization data not available for instance {instance_id}")

    # Get instance health and CPU utilization for cluster2
    print("\n--- Cluster2 (Target Group 2) ---")
    instance_health_cluster2 = get_instance_health(elb_client, target_group_arn_cluster2)
    if instance_health_cluster2:
        for target in instance_health_cluster2:
            instance_id = target['Target']['Id']
            health_status = target['TargetHealth']['State']
            print(f"Instance {instance_id} health: {health_status}")

            # Get CPU utilization
            cpu_utilization = get_cpu_utilization(cloudwatch_client, instance_id)
            if cpu_utilization is not None:
                print(f"Instance {instance_id} CPU utilization: {cpu_utilization:.2f}%")
            else:
                print(f"CPU utilization data not available for instance {instance_id}")

    async with aiohttp.ClientSession() as session:
        # Measure time for /cluster1
        start_time_cluster1 = time.time()
        tasks_cluster1 = [call_endpoint_http(session, i, "/cluster1", dns_name) for i in range(num_requests)]
        await asyncio.gather(*tasks_cluster1)
        end_time_cluster1 = time.time()

        # Measure time for /cluster2
        start_time_cluster2 = time.time()
        tasks_cluster2 = [call_endpoint_http(session, i, "/cluster2", dns_name) for i in range(num_requests)]
        await asyncio.gather(*tasks_cluster2)
        end_time_cluster2 = time.time()

    print(f"\nTotal time taken for /cluster1: {end_time_cluster1 - start_time_cluster1:.2f} seconds")
    print(f"Average time per request for /cluster1: {(end_time_cluster1 - start_time_cluster1) / num_requests:.4f} seconds")

    print(f"\nTotal time taken for /cluster2: {end_time_cluster2 - start_time_cluster2:.2f} seconds")
    print(f"Average time per request for /cluster2: {(end_time_cluster2 - start_time_cluster2) / num_requests:.4f} seconds")


if __name__ == "__main__":
    asyncio.run(main())
