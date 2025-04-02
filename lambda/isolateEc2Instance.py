# Version 2.1 - Added rollback scheduling via EventBridge Scheduler and improved logging
import boto3
import logging
import datetime
import json

stepfunctions = boto3.client('stepfunctions')
logger = logging.getLogger()
logger.setLevel(logging.INFO)

sns = boto3.client('sns')
SNS_TOPIC_ARN = 'arn:aws:sns:us-east-1:074521626635:SecurityAlertTopic'

def lambda_handler(event, context):
    ec2 = boto3.client('ec2')

    # Try to extract the instance ID from the actual event (update this logic as needed)
    instance_id = event.get('detail', {}).get('instance-id', 'i-0158afc81c9b032c4') # Default to a known instance ID

    logger.info(f"Attempting to isolate EC2 instance: {instance_id}")

    ssm = boto3.client('ssm')

    # Fetch current security groups for the instance
    response = ec2.describe_instances(InstanceIds=[instance_id])
    original_sg_ids = [
        sg['GroupId']
        for sg in response['Reservations'][0]['Instances'][0]['SecurityGroups']
    ]

    # Store original SGs in Parameter Store
    ssm.put_parameter(
        Name=f"/ec2/original_sg/{instance_id}",
        Value=",".join(original_sg_ids),
        Type="String",
        Overwrite=True
    )

    try:
        ec2.modify_instance_attribute(
            InstanceId=instance_id,
            Groups=['sg-037a81e6b749df305'] # My actual security group ID
        )
        msg = f"EC2 instance {instance_id} has been isolated."
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=msg,
            Subject='Security Alert: EC2 Instance Isolated'
        )
        logger.info(msg)

        # Trigger Step Function to handle rollback delay
        state_machine_arn = "arn:aws:states:us-east-1:074521626635:stateMachine:RollbackAfter15Minutes"
        try:
            stepfunctions.start_execution(
                stateMachineArn=state_machine_arn,
                input=json.dumps({"detail": {"instance-id": instance_id}})
            )
            logger.info(f"Step Function triggered for rollback of instance {instance_id}")
        except Exception as e:
            logger.error(f"Failed to start Step Function for rollback: {str(e)}")

    except Exception as e:
        error_msg = f"Failed to isolate EC2 instance {instance_id}: {str(e)}"
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=error_msg,
            Subject='Security Alert: EC2 Instance Isolation Failed'
        )
        logger.error(error_msg)
        raise
    return {
        'status': 'done',
        'instance': instance_id
    }