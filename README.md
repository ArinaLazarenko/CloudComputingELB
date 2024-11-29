<a id="readme-top"></a>

<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#requirements">Requirements</a>
      <a href="#installation">Installation</a>
      <a href="#components">Components</a>
      <ul>
        <li><a href="#globals">Globals</a></li>
        <li><a href="#instance_setup">Instance Setup</a></li>
        <li><a href="#elb_setup">ELB Setup</a></li>
        <li><a href="#benchmarking">Benchmarking</a></li>
        <li><a href="#health_check">Health Check</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#testing">Testing</a></li>
    <li><a href="#troubleshooting">Troubleshooting</a></li>
  </ol>
</details>


## Requirements

- **Python 3.x**: Ensure that you have Python installed on your machine.
- **Boto3**: AWS SDK for Python.
- **Paramiko**: For SSH connections to the EC2 instances.
- **Requests**: To handle HTTP requests for health checks.


To install the necessary packages, run:
```sh 
pip install boto3 paramiko requests
```
## Installation

1. Clone the repository to your local machine:
```sh 
git clone <repository_url>
cd <repository_directory>
```
2. Create a file named ```vpc_id.txt``` and ```subnet_id.txt``` in the AWS configuration folder ```(/home/.aws/)``` with your VPC ID and Subnet ID, respectively.
3. Ensure that your AWS credentials are configured properly, either by setting environment variables or using the AWS CLI.

## Components

### Globals
- **globals.py:** Contains global variables such as file paths, security group names, and target group names.

### Instance Setup
- **instance_setup.py:** Responsible for creating EC2 instances and security groups. It includes:
    - ```createSecurityGroup(vpc_id, group_name):``` Creates a security group and configures ingress rules.
    - ```createInstance(...):``` Creates an EC2 instance based on specified parameters.
### ELB Setup
- **elb_setup.py:** Handles the configuration of the Elastic Load Balancer and target groups, ensuring proper routing of traffic to the EC2 instances.

### Benchmarking
- **benchmark.py:** Conducts performance benchmarks on the instances to assess their capabilities and responsiveness.

### Health Check
- **test_instances_response.py:** Checks the health of EC2 instances by sending HTTP requests to a specified port and verifying responses.

## Usage
1. **Configure AWS Credentials:**
   - Set up your AWS credentials on your local machine using the AWS CLI or environment variables.

2. **Edit the `globals.py` File:**
   - Open the `globals.py` file and fill in the constants with the appropriate relative paths required by your project.

3. **Insert AWS Credentials in the `elb_userdata.sh` File:**
   - Open the `elb_userdata.sh` script and insert your AWS credentials in the following format:
     ```bash
     aws_access_key_id=[INSERT]
     aws_secret_access_key=[INSERT]
     aws_session_token=[INSERT]
     ```

4. **Make the `run_all.sh` Script Executable:**
   - In the terminal, run the following command to give execution permissions to the `run_all.sh` script:
   - 
     ```bash
     chmod +x run_all.sh
     ```

5. **Run the Bash Script:**
   - After making the script executable, run it using the following command:
     ```bash
     ./run_all.sh
     ```

6. **Check the Benchmarking Results:**
   - Once the script has completed running, the benchmarking results will be saved to a file named `benchmark_results.txt`. You can open or review this file for performance data.

## Testing
- After instances are created, the health status of each instance can be tested by running:
```sh 
python3 test_instances_response.py
```

## Troubleshooting
- If you encounter issues during instance creation:
  - Verify AWS credentials and permissions.
  - Ensure the specified VPC and subnet IDs are correct.
  - Check the security group settings.
- If health checks fail:
  - Confirm that the application is running on the instances.
  - Verify that the security group allows inbound traffic on the specified port (8000).

