# 🔐 AWS Auto-Remediation Platform

A serverless infrastructure that detects, isolates, and automatically remediates security threats on EC2 instances. Built entirely with AWS-native services and Python.

---

## 📦 Features

- ✅ **Automatic EC2 Isolation:** Moves compromised instances into a restrictive security group.
- ✅ **Step Function Rollback:** After 15 minutes, restores the original SG using a Step Function.
- ✅ **CloudWatch Monitoring:** Real-time Lambda metrics in a centralized dashboard.
- ✅ **SNS Alerts:** Emails your team when rollback completes.
- ✅ **SSM Cleanup:** Deletes temporary parameters after rollback to keep things clean.

---

## 📁 Project Structure

```
aws-auto-remediation/
├── lambda/
│   ├── isolateEc2Instance.py         # Lambda for isolating EC2 + triggering rollback
│   └── rollbackIsolation.py          # Lambda for restoring original security groups
├── infra/
│   ├── dashboard.json                # CloudWatch dashboard config
│   └── step-function-definition.json # State machine to wait 15 minutes before rollback
├── test-events/
│   ├── isolate-test.json             # Test payload for isolate function
│   └── rollback-test.json            # Test payload for rollback function
├── .gitignore
└── README.md
```

---

## 🚀 Deployment Instructions

### 1️⃣ Deploy Lambda Functions

```bash
# isolate function
cd lambda
zip isolate.zip isolateEc2Instance.py
aws lambda update-function-code \
  --function-name isolateEc2Instance \
  --zip-file fileb://isolate.zip \
  --region us-east-1

# rollback function
zip rollback.zip rollbackIsolation.py
aws lambda update-function-code \
  --function-name rollbackIsolation \
  --zip-file fileb://rollback.zip \
  --region us-east-1
```

---

### 2️⃣ Deploy Step Function (15-Min Rollback Delay)

```bash
aws stepfunctions create-state-machine \
  --name RollbackAfter15Minutes \
  --definition file://infra/step-function-definition.json \
  --role-arn arn:aws:iam::<your-account-id>:role/LambdaEC2RemediationRole \
  --region us-east-1
```

---

### 3️⃣ Deploy CloudWatch Dashboard

```bash
aws cloudwatch put-dashboard \
  --dashboard-name SecurityAutomationDashboard \
  --dashboard-body file://infra/dashboard.json \
  --region us-east-1
```

---

## 📩 Example Test Payloads

### isolate-test.json

```json
{
  "detail": {
    "instance-id": "i-xxxxxxxxxxxxxxxxx"
  }
}
```

### rollback-test.json

```json
{
  "detail": {
    "instance-id": "i-xxxxxxxxxxxxxxxxx"
  }
}
```

---

## 🔐 Required IAM Permissions

Your Lambda role (`LambdaEC2RemediationRole`) should include:

```json
{
  "Effect": "Allow",
  "Action": [
    "ec2:ModifyInstanceAttribute",
    "ssm:PutParameter",
    "ssm:GetParameter",
    "ssm:DeleteParameter",
    "sns:Publish",
    "states:StartExecution",
    "lambda:InvokeFunction"
  ],
  "Resource": "*"
}
```

Your trust policy must allow:

```json
{
  "Effect": "Allow",
  "Principal": {
    "Service": [
      "lambda.amazonaws.com",
      "states.amazonaws.com"
    ]
  },
  "Action": "sts:AssumeRole"
}
```

---

## 🧠 Inspiration

Built to automate security response in cloud environments with minimal human intervention. Designed to be extensible with GuardDuty, Config Rules, and advanced workflows.

---

## 👤 Author

**Frantz Banks**  
Built with ❤️, Python, and a whole lot of AWS 💪

---

## 📜 License

MIT License. Use it, extend it, secure your cloud 🚀
