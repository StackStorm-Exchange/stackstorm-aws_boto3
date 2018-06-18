# AWS Integration Pack

This pack uses boto3 actions in StackStorm dynamically. It has the following features:

- Uses boto3 configurations. Find more information on boto3 configuration in [boto3 documentation](http://boto3.readthedocs.io/en/latest/guide/quickstart.html#configuration). 
- Ability to run cross region actions.
- Ability to run cross account actions.

## Prerequisites

AWS and Stackstorm, up and running.

## Boto3 documentation

Boto3 contains detailed documentation and examples on each service. See more about available services here:  http://boto3.readthedocs.io/en/latest/reference/services/index.html

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
aws ec2 describe-vpcs --region "us-west-1"
```

Then go ahead and install aws pack. `aws_boto3.boto3action` is ready to use, without additional configurations.

```
st2 run aws.boto3action service="ec2" action_name="describe_vpcs" region="us-west-1"
```

Let’s assume there is a boto3 profile name `production`. Use it like this:

```
st2 run aws_boto3.boto3action service="ec2" action_name="describe_vpcs" region="us-west-1" env="AWS_PROFILE=production"
```

See the Boto3 documentation for more [information on profiles](http://boto3.readthedocs.io/en/latest/guide/configuration.html#shared-credentials-file).


## Example workflow - Create VPC

action/create_vpc.yaml

```yaml
name: "create_vpc"
runner_type: "mistral-v2"
description: "Create VPC with boto3action"
enabled: true
entry_point: "workflows/create_vpc.yaml"
parameters:
  cidr_block:
    type: "string"
    description: "VPC CIDR block"
    required: true
  region:
    type: "string"
    description: "Region to create VPC"
    required: true
  subnet_cidr_block:
    type: "string"
    description: "Subnet CIDR block"
    required: true
  availability_zone:
    type: "string"
    description: "Availability zone to create subnet"
    required: true

```

action/workflows/create_vpc.yaml


```yaml
---
version: '2.0'
aws.create_vpc:
    type: direct
    description: "Create VPC with boto3action"
    input:
        - cidr_block
        - region
        - subnet_cidr_block
        - availability_zone
    tasks:
      create_vpc:
        action: aws_boto3.boto3action
        input:
          service: ec2
          action_name: create_vpc
          region: <% $.region %>
          params: <% dict(CidrBlock => $.cidr_block, InstanceTenancy => "default") %>
        publish:
          vpc_id: <% task(create_vpc).result.result.Vpc.VpcId %>
        on-success:
          - create_subnet
          - create_igw
          
      create_subnet:
        action: aws_boto3.boto3action
        input:
          service: ec2
          action_name: create_subnet
          region: <% $.region %>
          params: <% dict(AvailabilityZone => $.availability_zone, CidrBlock => $.subnet_cidr_block, VpcId => $.vpc_id) %>
        publish:
          subnet_id: <% task(create_subnet).result.result.Subnet.SubnetId %>
        on-success:
          - create_route_table

      create_igw:
        action: aws_boto3.boto3action
        input:
          service: ec2
          action_name: create_internet_gateway
          region: <% $.region %>
        publish:
          igw_id: <% task(create_igw).result.result.InternetGateway.InternetGatewayId %>
        on-success:
          - attach_igw

      attach_igw:
        action: aws_boto3.boto3action
        input:
          service: ec2
          action_name: attach_internet_gateway
          region: <% $.region %>
          params: <% dict(VpcId => $.vpc_id, InternetGatewayId => $.igw_id) %>
        on-success:
          - create_route_igw

      create_route_table:
        action: aws_boto3.boto3action
        input:
          service: ec2
          action_name: create_route_table
          region: <% $.region %>
          params: <% dict(VpcId => $.vpc_id) %>
        publish:
          route_table_id: <% task(create_route_table).result.result.RouteTable.RouteTableId %>
        on-success:
          - attach_route_tables

      attach_route_tables:
        action: aws_boto3.boto3action
        input:
          service: ec2
          action_name: associate_route_table
          region: <% $.region %>
          params: <% dict(SubnetId => $.subnet_id, RouteTableId => $.route_table_id) %>
        on-success:
          - create_route_igw

      create_route_igw:
        join: 2
        action: aws_boto3.boto3action
        input:
          service: ec2
          action_name: create_route
          region: <% $.region %>
          params: <% dict(RouteTableId => $.route_table_id, GatewayId => $.igw_id, DestinationCidrBlock => '0.0.0.0/0') %>
```

Run it:

```
st2 run aws_boto3.create_vpc cidr_block="172.18.0.0/16" region="us-west-2" availability_zone="us-west-2b" subnet_cidr_block="172.18.0.0/24"
```

## Create VPC workflow with assume_role

Let’s assume we have two aws accounts. First aws account, 123456, is already configured to use boto3. Second aws account, 456789, has a `IAM` role `st2_role`. We can assume this role, then use `create_vpc` workflow to create vpc in aws account 456789.

action/workflows/create_vpc.yaml

```yaml
---
version: '2.0'
aws_boto3.create_vpc:
    type: direct
    description: "Create VPC with boto3action"
    input:
        - cidr_block
        - region
        - subnet_cidr_block
        - availability_zone
    tasks:
      assume_role:
        action: aws_boto3.assume_role
        input:
          role_arn: “arn:aws:iam:456789:role/st2_role”
        publish:
          credentials: <% task(assume_role).result.result %>
        on-success:
          - create_vpc

      create_vpc:
        action: aws_boto3.boto3action
        input:
          service: ec2
          action_name: create_vpc
          region: <% $.region %>
          params: <% dict(CidrBlock => $.cidr_block, InstanceTenancy => "default") %>
          credentials: <% $.credentials %>
        publish:
          vpc_id: <% task(create_vpc).result.result.Vpc.VpcId %>
        on-success:
          - create_subnet
          - create_igw
          
      create_subnet:
        action: aws_boto3.boto3action
        input:
          service: ec2
          action_name: create_subnet
          region: <% $.region %>
          params: <% dict(AvailabilityZone => $.availability_zone, CidrBlock => $.subnet_cidr_block, VpcId => $.vpc_id) %>
          credentials: <% $.credentials %>
        publish:
          subnet_id: <% task(create_subnet).result.result.Subnet.SubnetId %>
        on-success:
          - create_route_table

      create_igw:
        action: aws_boto3.boto3action
        input:
          service: ec2
          action_name: create_internet_gateway
          region: <% $.region %>
          credentials: <% $.credentials %>
        publish:
          igw_id: <% task(create_igw).result.result.InternetGateway.InternetGatewayId %>
        on-success:
          - attach_igw

      attach_igw:
        action: aws_boto3.boto3action
        input:
          service: ec2
          action_name: attach_internet_gateway
          region: <% $.region %>
          params: <% dict(VpcId => $.vpc_id, InternetGatewayId => $.igw_id) %>
          credentials: <% $.credentials %>
        on-success:
          - create_route_igw

      create_route_table:
        action: aws_boto3.boto3action
        input:
          service: ec2
          action_name: create_route_table
          region: <% $.region %>
          params: <% dict(VpcId => $.vpc_id) %>
          credentials: <% $.credentials %>
        publish:
          route_table_id: <% task(create_route_table).result.result.RouteTable.RouteTableId %>
        on-success:
          - attach_route_tables

      attach_route_tables:
        action: aws_boto3.boto3action
        input:
          service: ec2
          action_name: associate_route_table
          region: <% $.region %>
          params: <% dict(SubnetId => $.subnet_id, RouteTableId => $.route_table_id) %>
          credentials: <% $.credentials %>
        on-success:
          - create_route_igw

      create_route_igw:
        join: 2
        action: aws_boto3.boto3action
        input:
          service: ec2
          action_name: create_route
          region: <% $.region %>
          params: <% dict(RouteTableId => $.route_table_id, GatewayId => $.igw_id, DestinationCidrBlock => '0.0.0.0/0') %>
          credentials: <% $.credentials %>
```
