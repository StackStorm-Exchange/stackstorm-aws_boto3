import json
import boto3

from st2common.runners.base_action import Action
from lib.util import json_serial


# pylint: disable=too-few-public-methods
class Boto3ActionRunner(Action):
    def run(self, service, region, action_name, credentials, params):

        if credentials is not None:

            # This is backwards compatibility for a bug from the boto3 branch
            # of the aws pack.
            if 'Credentials' in credentials:
                credentials = credentials['Credentials']

            session_kwargs['aws_access_key_id'] = credentials['AccessKeyId']
            session_kwargs['aws_secret_access_key'] = credentials['SecretAccessKey']
            session_kwargs['aws_session_token'] = credentials['SessionToken']

        session = boto3.Session(**session_kwargs)
        client = session.client(service, region_name=region)

        if client is None:
            return False, 'boto3 client creation failed'

        if params is not None:
            response = getattr(client, action_name)(**params)
        else:
            response = getattr(client, action_name)()

        response = json.loads(json.dumps(response, default=json_serial))
        return True, response
