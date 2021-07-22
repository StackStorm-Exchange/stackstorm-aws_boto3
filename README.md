# AWS Integration Pack

This pack uses boto3 actions in StackStorm dynamically. It has the following features:

- Uses boto3 configurations. Find more information on boto3 configuration in
  [boto3 documentation](http://boto3.readthedocs.io/en/latest/guide/quickstart.html#configuration).
- Ability to run cross region actions.
- Ability to run cross account actions.

## Prerequisites

AWS and Stackstorm, up and running.

## Boto3 documentation

Boto3 contains detailed documentation and examples on each service. See more about available services
here: http://boto3.readthedocs.io/en/latest/reference/services/index.html

## Setup

### Install AWS_boto3 pack on StackStorm

1. Install the [AWS_boto3 pack](https://github.com/stackstorm-exchange/stackstorm-aws_boto3):

    ```
    # Install AWS
    st2 pack install aws_boto3

    # Check it
    st2 action list -p aws_boto3
    ```

### Configuration

This pack currently has no configuration ([See issue #4](https://github.com/StackStorm-Exchange/stackstorm-aws_boto3/issues/4)).

The simplest way to configure and test boto3 is to use `awscli`.

```
pip install awscli
aws configure
aws ec2 describe-vpcs --region "eu-west-1"
```

Or you can pass `aws_access_key_id` and `aws_secret_access_key` in as parameters to `assume_role` along with optional
MFA parameters.

Then go ahead and install aws pack and then `aws_boto3.boto3action` is ready to use, without additional configurations.

```
st2 run aws_boto3.boto3action service="ec2" action_name="describe_vpcs" region="us-west-1"
```

Let’s assume there is a boto3 profile name `production`. Use it like this:

```
st2 run aws_boto3.boto3action service="ec2" action_name="describe_vpcs" region="us-west-1" env="AWS_PROFILE=production"
```

See the Boto3 documentation for more [information on profiles](http://boto3.readthedocs.io/en/latest/guide/configuration.html#shared-credentials-file).

## Example workflow - Scale up autoscaling group (using parameters)

### aws_boto3.boto3action

```
st2 run aws_boto3.boto3action service="autoscaling" region="us-east-1" action_name="set_desired_capacity" params='{"AutoScalingGroupName": "my_asg","DesiredCapacity": 2}'
```


## Example workflow - Create instance

### aws_boto3.create_instance

Create an EC2 instance with defined keypair, subnet and security group:

```
st2 run aws_boto3.create_instance \
  region=us-east-1 \
  ImageId=ami-1234abcd \
  KeyName=deployment-key \
  SubnetId=subnet-5678efef \
  SecurityGroupIds='["sg-dcba9100"]'
```

Create an instance and assign tags:

```
st2 run --auto-dict aws_boto3.create_instance \
  ImageId=ami-1234abcd \
  Tags=Name:my-instance \
  Tags=Owner:me@example.com
```

## Example workflow - Create VPC

### aws_boto3.create_vpc

Create an VPC and a single subnet, run the following command:

```
st2 run aws_boto3.create_vpc \
  cidr_block="172.18.0.0/16" \
  region="eu-west-1" \
  availability_zone="us-west-2b" \
  subnet_cidr_block="172.18.0.0/24"
```

## Create VPC workflow with assume_role

Let’s assume we have two aws accounts. First aws account (`123456`) is already configured to use boto3. The second aws
account (`456789`) has a `IAM` role `st2_role` assigned to the ST2 instance. We can assume this role, then
use `create_vpc` workflow to create vpc in aws account 456789.

```
st2 run aws_boto3.create_vpc \
  role_arn="arn:aws:iam:456789:role/st2_role" \
  cidr_block="172.18.0.0/16" \
  region="eu-west-1" \
  availability_zone="eu-west-1a" \
  subnet_cidr_block="172.18.0.0/24"
```

If you have your own IAM account (`oliver`) in `123456` and are allowed to switch roles to `st2_role` within
account `456789` (plus and have exported variables for `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`) you
could run the following command to create a VPC:

```
st2 run aws_boto3.create_vpc_assume_role role_arn="arn:aws:iam::456789:role/st2_role" \
  region="eu-west-1" cidr_block="172.18.0.0/16" availability_zone="eu-west-1a" subnet_cidr_block="172.18.0.0/24" \
  aws_access_key_id="${AWS_ACCESS_KEY_ID}" aws_secret_access_key="${AWS_SECRET_ACCESS_KEY}" \
  serial_number="arn:aws:iam::123456:mfa/oliver" use_mfa=True token_code=123456
```
