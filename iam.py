import boto3
iam = boto3.client('iam')

#assudmes that roles are attached directly to user not via group assignment
policies=iam.list_attached_user_policies(UserName='ScanAgent')

role_policies = list()
for policy in policies['AttachedPolicies']:
    role_policies.append(policy['PolicyArn'])
    print(policy['PolicyArn'])
    