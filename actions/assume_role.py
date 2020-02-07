import json
import os
import boto3
from botocore.exceptions import ClientError

from st2common.runners.base_action import Action

from lib.util import json_serial


# pylint: disable=too-few-public-methods
class Boto3AssumeRoleRunner(Action):
    def run(self, role_arn,
            policy=None, duration=3600, external_id=None,
            aws_access_key_id=None, aws_secret_access_key=None,
            use_mfa=False, serial_number=None, token_code=None):

        success = False
        result = dict()

        sts_kwargs = dict()

        if aws_access_key_id and aws_secret_access_key:
            sts_kwargs['aws_access_key_id'] = aws_access_key_id
            sts_kwargs['aws_secret_access_key'] = aws_secret_access_key

        client = boto3.client('sts', **sts_kwargs)

        # Dynamically build the RoleSessionName with the action execution so we know it's unique.
        role_session_name = "ST2AssumeRole_{}".format(os.environ['ST2_ACTION_EXECUTION_ID'])

        kwargs = {
            'RoleArn': role_arn,
            'RoleSessionName': role_session_name,
            'DurationSeconds': duration,
        }

        if policy is not None:
            kwargs['Policy'] = policy

        if external_id is not None:
            kwargs['ExternalId'] = external_id

        if use_mfa:
            kwargs['SerialNumber'] = serial_number
            kwargs['TokenCode'] = token_code

        try:
            response = client.assume_role(**kwargs)
        except ClientError as e:
            result['error'] = str(e)
        else:
            response = json.loads(json.dumps(response, default=json_serial))
            result['AssumedRoleUser'] = response['AssumedRoleUser']
            result['Credentials'] = response['Credentials']
            success = True

        return success, result
