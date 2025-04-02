import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    ec2 = boto3.client('ec2')
    ssm = boto3.client('ssm')

    instance_id = event.get('detail', {}).get('instance-id', 'i-0158afc81c9b032c4')  # Default to a known instance ID
    logger.info(f"Attempting to rollback isolation for EC2 instance: {instance_id}")

    try:
        # Fetch the original security group IDs from Parameter Store
        response = ssm.get_parameter(
            Name=f"/ec2/original_sg/{instance_id}"
        )
        original_sg_ids = response['Parameter']['Value'].split(',')

        # Apply the original security groups to the instance
        ec2.modify_instance_attribute(
            InstanceId=instance_id,
            Groups=original_sg_ids
        )

        logger.info(f"Successfully restored SGs for instance {instance_id}: {original_sg_ids}")
        # Notify rollback completion
        msg = f"Rollback complete: EC2 instance {instance_id} has been restored to original security groups."
        sns = boto3.client('sns')
        sns.publish(
            TopicArn='arn:aws:sns:us-east-1:074521626635:SecurityAlertTopic',
            Message=msg,
            Subject='Security Notice: EC2 Rollback Completed'
        )
        logger.info(msg)

        # Cleanup parameter from Parameter Store
        try:
            ssm.delete_parameter(Name=f"/ec2/original_sg/{instance_id}")
            logger.info(f"Deleted SSM parameter for {instance_id}")
        except Exception as cleanup_error:
            logger.warning(f"Failed to delete SSM parameter for {instance_id}: {str(cleanup_error)}")
    except Exception as e:
        logger.error(f"Failed to restore SGs for instance {instance_id}: {str(e)}")
        raise
    return {
        'status': 'done',
        'instance': instance_id
    }