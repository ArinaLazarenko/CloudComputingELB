import boto3


# Define the security group name and key name
security_group_name = 'SecurityGroup'
key_name = 'key'

'''
Description: Terminates all running EC2 instances and returns their instance IDs.
Outputs: instance_ids (list) - A list of terminated instance IDs.
'''
def terminate_instances():
    ec2 = boto3.client('ec2')
    response = ec2.describe_instances(
        Filters=[
            {'Name': 'instance-state-name', 'Values': ['running']}
        ]
    )
    instance_ids = []
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            instance_ids.append(instance['InstanceId'])
            ec2.terminate_instances(InstanceIds=[instance['InstanceId']])
            print(f"Terminating instance: {instance['InstanceId']}")
    return instance_ids

'''
Description: Waits for the specified EC2 instances to fully terminate before proceeding.
Inputs: instance_ids (list) - A list of EC2 instance IDs to wait for termination.
'''
def wait_for_termination(instance_ids: list):
    ec2 = boto3.client('ec2')
    print('Waiting for instances to terminate.')
    waiter = ec2.get_waiter('instance_terminated')
    waiter.wait(InstanceIds=instance_ids)
    print("All instances terminated.")

'''
Description: Deletes the specified key pair if it exists in the AWS account.
'''
def delete_key_pairs():
    ec2 = boto3.client('ec2')
    response = ec2.describe_key_pairs()
    for key_pair in response['KeyPairs']:
        if key_pair['KeyName'] == key_name:
            ec2.delete_key_pair(KeyName=key_name)
            print(f"Deleted key pair: {key_name}")

'''
Description: Deletes the specified security group by its name if it exists in the AWS account.
'''
def delete_security_group():
    ec2 = boto3.client('ec2')
    
    # Describe the security group to get its ID
    response = ec2.describe_security_groups(
        Filters=[
            {'Name': 'group-name', 'Values': [security_group_name]}
        ]
    )
    
    for sg in response['SecurityGroups']:
        sg_id = sg['GroupId']
        
        try:
            ec2.delete_security_group(GroupId=sg_id)
            print(f"Deleted security group: {sg_id}")
        except ec2.exceptions.ClientError as e:
            print(f"Failed to delete security group {sg_id}: {e}")

'''
Description: Deletes all load balancers, along with their associated listeners, rules, and target groups.
'''
def delete_load_balancers():
    elb = boto3.client('elbv2')
    response = elb.describe_load_balancers()
    
    for lb in response['LoadBalancers']:
        lb_arn = lb['LoadBalancerArn']
        
       # Delete listeners and rules
        try:
            listeners = elb.describe_listeners(LoadBalancerArn=lb_arn)
            for listener in listeners['Listeners']:
                rules = elb.describe_rules(ListenerArn=listener['ListenerArn'])
                for rule in rules['Rules']:
                    if not rule['IsDefault']:
                        elb.delete_rule(RuleArn=rule['RuleArn'])
                        print(f"Deleted rule: {rule['RuleArn']}")
                elb.delete_listener(ListenerArn=listener['ListenerArn'])
                print(f"Deleted listener: {listener['ListenerArn']}")
        except elb.exceptions.ListenerNotFoundException:
            print(f"No listeners found for load balancer: {lb_arn}")
        
        # Delete target groups
        try:
            target_groups = elb.describe_target_groups(LoadBalancerArn=lb_arn)
            for tg in target_groups['TargetGroups']:
                elb.delete_target_group(TargetGroupArn=tg['TargetGroupArn'])
                print(f"Deleted target group: {tg['TargetGroupArn']}")
        except elb.exceptions.TargetGroupNotFoundException:
            print(f"No target groups found for load balancer: {lb_arn}")

          # Delete the load balancer
        elb.delete_load_balancer(LoadBalancerArn=lb_arn)
        print(f"Deleted load balancer: {lb_arn}")

'''
Description: Deletes all target groups in the AWS account.
'''
def delete_target_groups():
    elb = boto3.client('elbv2')
    target_groups = elb.describe_target_groups()
    for tg in target_groups['TargetGroups']:
        elb.delete_target_group(TargetGroupArn=tg['TargetGroupArn'])
        print(f"Deleted target group: {tg['TargetGroupArn']}")

'''
Description: # Main function to execute the steps
'''
def main():
    instance_ids = terminate_instances()
    wait_for_termination(instance_ids)
    delete_load_balancers()
    delete_target_groups()
    delete_key_pairs()
    delete_security_group()

if __name__ == "__main__":
    main()