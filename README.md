# Create a Development Environment with Okteto, Kubernetes, and AWS Services

This is an example of how to configure and deploy a development environment that includes polyglot microservices, an AWS SQS queue, and an S3 bucket. The AWS infrastructure is deployed using Terraform.

## Architecture

📊 **[View Interactive Architecture Diagram](./architecture-diagram.md)**

The architecture demonstrates a cloud-native development environment spanning Okteto (Kubernetes) and AWS services, featuring polyglot microservices for "The Oktaco Shop" food ordering application.

## Run the demo application in Okteto

### Prerequisites:
1. Okteto CLI 3.0 or newer
1. An AWS account
1. An Okteto account ([Sign-up](https://www.okteto.com/try-free/) for 30 day, self-hosted free trial)
1. Create a set of IAM keys for your AWS account (If you are using Okteto Self-Hosted, you can directly assign an AWS Role)
1. Create the following Okteto secrets:

        AWS_ACCESS_KEY_ID: The Acces Key ID of your IAM user
        AWS_SECRET_ACCESS_KEY: The Secret Acces Key of your IAM user
        AWS_REGION: The region in AWS you would like to use for the external resources

Make sure this AWS user has permissions to create, read from, and delete the following AWS services:

- SQS Queues
- S3 Buckets

> Alternatively if you are using Okteto Self-Hosted, you can configure your instance to use an AWS role instead of using an Access Key and Secret Access Key.

Once this is configured, anyone with access to your Okteto instance will be able to deploy an development environment automatically, including the required cloud infrastructure.


```
$ git clone https://github.com/okteto/external-resources-tf-aws
$ cd external-resources-aws
$ okteto context use $OKTETO_URL
$ okteto deploy
```

## Develop on the Menu microservice

```
$ okteto up menu
```

## Develop on the Kitchen microservice

```
$ okteto up kitchen
```

## Develop on the Result microservice

```
$ okteto up check
```

## Run the end to end tests

To run the e2d tests directly in Okteto, execute the command below.

```
$ okteto test e2e
```

## Notes

This isn't an example of a properly architected perfectly designed distributed app... it's a simple
example of the various types of pieces and languages you might see (queues, persistent data, etc), and how to
deal with them in Okteto.

Happy coding!
