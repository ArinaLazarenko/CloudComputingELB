
import time
import os
import globals as g
import boto3
import stat
import paramiko

import instance_setup as ic
import elb_setup as elbs
import benchmark as bm

'''
Description: Connects to an EC2 instance via SSH and runs a specified Python script.
Inputs: 
    instance_ip (str) - The public IP address of the EC2 instance.
    pem_file_path (str) - The file path to the PEM file used for SSH authentication.
Outputs: None (prints connection status and script execution results).
'''
def ssh_and_run_script(instance_ip: str, pem_file_path: str):
    try:
        print(f"Connecting to {instance_ip} using SSH...")
        # Initialize SSH client
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Connect to the instance
        ssh.connect(instance_ip, username='ubuntu', key_filename=pem_file_path)
        
        print("Connected! Now running 'python3 elb_traffic_manager.py'...")
        
        # Run the command to execute the Python script
        stdin, stdout, stderr = ssh.exec_command('python3 elb_traffic_manager.py')
        
        # Close the SSH connection
        ssh.close()
        print("SSH connection closed.")

    except Exception as e:
        print(f"An error occurred during SSH: {str(e)}")


if __name__ == "__main__":
    print("RUNNING MAIN AUTOMATED SCRIPT")    

    pem_file_path = g.pem_file_path


    # Create EC2 Client
    session = boto3.Session()
    ec2 = session.resource('ec2')

    # Read VPC and Subnet IDs from files
    with open(f'{g.aws_folder_path}/vpc_id.txt', 'r') as file:
        vpc_id = file.read().strip()

    with open(f'{g.aws_folder_path}/subnet_id.txt', 'r') as file:
        subnet_id = file.read().strip()


    # Delete keypair with same name, USED IN TESTING
    # ec2.KeyPair("key_name").delete()

    # Create a new key pair and save the .pem file
    key_pair = ec2.create_key_pair(KeyName='key_name')

    # Change security to be able to read
    os.chmod(pem_file_path, stat.S_IWUSR)

    # Save the private key to a .pem file
    with open(pem_file_path, 'w') as pem_file:
        pem_file.write(key_pair.key_material)

    # Change file permissions to 400 to protect the private key
    os.chmod(pem_file_path, stat.S_IRUSR)

    # Create security group
    security_id = ic.createSecurityGroup(vpc_id, g.security_group_name)

    with open('bash_scripts/api_userdata.sh', 'r') as file:
        api_user_data = file.read()

    with open('bash_scripts/elb_userdata.sh', 'r') as file:
        elb_user_data = file.read()


    print("Creating instances...")
    # FastApi instances - 3x large & 5x micro
    ic.createInstance('t2.large', 2, 2, key_pair, security_id, subnet_id, api_user_data, "FastAPI-Instance") # For cluster1
    ic.createInstance('t2.micro', 2, 2, key_pair, security_id, subnet_id, api_user_data, "FastAPI-Instance") # For cluster2

    print("Waiting for instances to be up and running...")
    time.sleep(180)


    print("Setting up the ELB client and configuring the target groups...")
    # Sets up the ELB client and configures the target groups
    elbs.main()

    print("Waiting for ELB setup to be completed...")
    time.sleep(180)


    print("Creating the elb-EC2 instance and executes load-balance-script...")
    # EC2 Instance for the ELB logic - large (has to wait for every other instance to be up and running)
    elb_instance = ic.createInstance('t2.large', 1, 1, key_pair, security_id, subnet_id, elb_user_data, "ELB-Instance") # WAIT FOR THE INSTANCES TO BE UP!

    print("Waiting for ELB instance to be ready...")
    time.sleep(240)  # Adjust based on how long it takes for the instance to be fully available


    print("SSH into the ELB instance and run the script elb_traffic_manager script...")
    # Retrieve the public IP address from the instance object
    load_balancer_instance_ip = elb_instance[0].public_ip_address
    print(f"Load Balancer Instance IP: {load_balancer_instance_ip}")


    # SSH into the load balancer instance and run the script
    ssh_and_run_script(load_balancer_instance_ip, pem_file_path)

    time.sleep(5)

    print("AUTOMATED SCRIPT COMPLETED!")
