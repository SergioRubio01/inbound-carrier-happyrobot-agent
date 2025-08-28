import * as pulumi from "@pulumi/pulumi";
import * as aws from "@pulumi/aws";
import * as awsx from "@pulumi/awsx";
import * as path from "path";

export interface ContainersArgs {
    vpc: aws.ec2.Vpc;
    privateSubnets: aws.ec2.Subnet[];
    ecsSecurityGroup: aws.ec2.SecurityGroup;
    databaseEndpoint: pulumi.Output<string>;
    databaseSecretArn: pulumi.Output<string>;
    environment: string;
    apiKey: string;
    enableHttps?: boolean; // Enable HTTPS for security headers
    tags: Record<string, string>;
}

export class ContainersComponent extends pulumi.ComponentResource {
    public readonly cluster: aws.ecs.Cluster;
    public readonly apiRepository: aws.ecr.Repository;
    public readonly taskRole: aws.iam.Role;
    public readonly executionRole: aws.iam.Role;
    public readonly apiTaskDefinition: aws.ecs.TaskDefinition;
    public readonly apiService: aws.ecs.Service;
    public readonly apiTargetGroup: aws.lb.TargetGroup;

    constructor(name: string, args: ContainersArgs, opts?: pulumi.ComponentResourceOptions) {
        super("happyrobot:containers", name, {}, opts);

        // Create ECS Cluster
        this.cluster = new aws.ecs.Cluster(`${name}-cluster`, {
            name: `${name}-cluster`,
            settings: [
                {
                    name: "containerInsights",
                    value: "enabled",
                },
            ],
            tags: {
                ...args.tags,
                Name: "happyrobot-fde",
            },
        }, { parent: this });

        // Create ECR repositories
        this.apiRepository = new aws.ecr.Repository(`${name}-api-repo`, {
            name: `${name}-api`,
            imageTagMutability: "MUTABLE",
            imageScanningConfiguration: {
                scanOnPush: true,
            },
            tags: {
                ...args.tags,
                Name: "happyrobot-api",
            },
        }, { parent: this });

        // Build and push Docker image to ECR
        // This will only rebuild if the Docker context or Dockerfile changes
        // Pulumi automatically tracks file changes and only rebuilds when necessary
        const apiImage = new awsx.ecr.Image(`${name}-api-image`, {
            repositoryUrl: this.apiRepository.repositoryUrl,
            context: path.resolve(__dirname, "../../../.."), // Path to the root of the project
            dockerfile: path.resolve(__dirname, "../../../../Dockerfile.api"),
            platform: "linux/amd64", // Ensure compatibility with Fargate
            // The image will be tagged with a hash of the build context
            // This ensures we only rebuild when source files actually change
            imageName: pulumi.interpolate`${this.apiRepository.repositoryUrl}:${args.environment}`,
            cacheFrom: {
                stages: ["build", "runtime"], // Cache intermediate build stages if your Dockerfile uses multi-stage builds
            },
            args: {
                // Build args if needed
                BUILDKIT_INLINE_CACHE: "1", // Enable inline cache for better caching
            },
        }, { parent: this });

        // Create lifecycle policies for ECR repositories
        new aws.ecr.LifecyclePolicy(`${name}-api-lifecycle`, {
            repository: this.apiRepository.name,
            policy: JSON.stringify({
                rules: [
                    {
                        rulePriority: 1,
                        description: "Keep last 10 images",
                        selection: {
                            tagStatus: "any",
                            countType: "imageCountMoreThan",
                            countNumber: 10,
                        },
                        action: {
                            type: "expire",
                        },
                    },
                ],
            }),
        }, { parent: this });


        // Create IAM role for task execution
        this.executionRole = new aws.iam.Role(`${name}-execution-role`, {
            name: `${name}-ecs-execution-role`,
            assumeRolePolicy: JSON.stringify({
                Version: "2012-10-17",
                Statement: [
                    {
                        Action: "sts:AssumeRole",
                        Effect: "Allow",
                        Principal: {
                            Service: "ecs-tasks.amazonaws.com",
                        },
                    },
                ],
            }),
            tags: {
                ...args.tags,
                Name: `${name}-ecs-execution-role`,
            },
        }, { parent: this });

        // Attach execution role policies
        new aws.iam.RolePolicyAttachment(`${name}-execution-policy`, {
            role: this.executionRole.name,
            policyArn: "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy",
        }, { parent: this });

        // Create custom policy for accessing Secrets Manager
        const secretsPolicy = new aws.iam.Policy(`${name}-secrets-policy`, {
            name: `${name}-ecs-secrets-policy`,
            description: "Policy for ECS tasks to access Secrets Manager",
            policy: args.databaseSecretArn.apply(secretArn => JSON.stringify({
                Version: "2012-10-17",
                Statement: [
                    {
                        Effect: "Allow",
                        Action: [
                            "secretsmanager:GetSecretValue",
                        ],
                        Resource: secretArn,
                    },
                ],
            })),
            tags: {
                ...args.tags,
                Name: `${name}-ecs-secrets-policy`,
            },
        }, { parent: this });

        new aws.iam.RolePolicyAttachment(`${name}-secrets-policy-attachment`, {
            role: this.executionRole.name,
            policyArn: secretsPolicy.arn,
        }, { parent: this });

        // Create IAM role for tasks (application permissions)
        this.taskRole = new aws.iam.Role(`${name}-task-role`, {
            name: `${name}-ecs-task-role`,
            assumeRolePolicy: JSON.stringify({
                Version: "2012-10-17",
                Statement: [
                    {
                        Action: "sts:AssumeRole",
                        Effect: "Allow",
                        Principal: {
                            Service: "ecs-tasks.amazonaws.com",
                        },
                    },
                ],
            }),
            tags: {
                ...args.tags,
                Name: `${name}-ecs-task-role`,
            },
        }, { parent: this });

        // Create CloudWatch log groups
        const apiLogGroup = new aws.cloudwatch.LogGroup(`${name}-api-logs`, {
            name: `/aws/ecs/${name}-api`,
            retentionInDays: args.environment === "prod" ? 30 : 7,
            tags: {
                ...args.tags,
                Name: `${name}-api-logs`,
            },
        }, { parent: this });


        // Create target groups (will be used by load balancer)
        this.apiTargetGroup = new aws.lb.TargetGroup(`${name}-api-tg`, {
            name: `${name}-api-tg`,
            port: 8000,
            protocol: "HTTP",
            vpcId: args.vpc.id,
            targetType: "ip",
            healthCheck: {
                enabled: true,
                healthyThreshold: 2,
                unhealthyThreshold: 3,
                timeout: 10,
                interval: 30,
                path: "/api/v1/health",
                matcher: "200",
                protocol: "HTTP",
                port: "traffic-port",
            },
            tags: {
                ...args.tags,
                Name: `${name}-api-tg`,
            },
        }, { parent: this });


        // Get business logic configuration
        const config = new pulumi.Config("happyrobot-fde");
        const maxLoadWeightLbs = config.get("maxLoadWeightLbs") || "80000";
        const maxReferenceNumberCounter = config.get("maxReferenceNumberCounter") || "99999";
        const maxRateAmount = config.get("maxRateAmount") || "999999.99";

        // API Task Definition
        this.apiTaskDefinition = new aws.ecs.TaskDefinition(`${name}-api-task`, {
            family: `${name}-api`,
            networkMode: "awsvpc",
            requiresCompatibilities: ["FARGATE"],
            cpu: "256",
            memory: "512",
            executionRoleArn: this.executionRole.arn,
            taskRoleArn: this.taskRole.arn,
            containerDefinitions: pulumi.all([
                apiImage.imageUri,
                args.databaseEndpoint,
                args.databaseSecretArn,
                apiLogGroup.name,
            ]).apply(([imageUri, dbEndpoint, secretArn, logGroupName]) => {
                const containerName = `${name}-api`;
                return JSON.stringify([
                {
                    name: containerName,
                    image: imageUri,
                    essential: true,
                    portMappings: [
                        {
                            containerPort: 8000,
                            protocol: "tcp",
                        },
                    ],
                    environment: [
                        {
                            name: "ENVIRONMENT",
                            value: args.environment,
                        },
                        {
                            name: "API_KEY",
                            value: args.apiKey,
                        },
                        {
                            name: "POSTGRES_HOST",
                            value: dbEndpoint.split(':')[0], // Extract hostname only
                        },
                        {
                            name: "POSTGRES_PORT",
                            value: "5432",
                        },
                        {
                            name: "POSTGRES_DB",
                            value: "happyrobot",
                        },
                        {
                            name: "ENABLE_HTTPS",
                            value: args.enableHttps ? "true" : "false",
                        },
                        {
                            name: "MAX_LOAD_WEIGHT_LBS",
                            value: maxLoadWeightLbs,
                        },
                        {
                            name: "MAX_REFERENCE_NUMBER_COUNTER",
                            value: maxReferenceNumberCounter,
                        },
                        {
                            name: "MAX_RATE_AMOUNT",
                            value: maxRateAmount,
                        },
                    ],
                    secrets: [
                        {
                            name: "POSTGRES_USER",
                            valueFrom: `${secretArn}:username::`,
                        },
                        {
                            name: "POSTGRES_PASSWORD",
                            valueFrom: `${secretArn}:password::`,
                        },
                    ],
                    logConfiguration: {
                        logDriver: "awslogs",
                        options: {
                            "awslogs-group": logGroupName,
                            "awslogs-region": aws.config.region!,
                            "awslogs-stream-prefix": "ecs",
                        },
                    },
                    healthCheck: {
                        command: ["CMD-SHELL", "curl -f http://localhost:8000/api/v1/health || exit 1"],
                        interval: 30,
                        timeout: 5,
                        retries: 3,
                        startPeriod: 60,
                    },
                },
            ]);
            }),
            tags: {
                ...args.tags,
                Name: `${name}-api-task`,
            },
        }, { parent: this });


        // API ECS Service
        this.apiService = new aws.ecs.Service(`${name}-api-service`, {
            name: `${name}-api-service`,
            cluster: this.cluster.id,
            taskDefinition: this.apiTaskDefinition.arn,
            launchType: "FARGATE",
            desiredCount: 1,
            platformVersion: "LATEST",

            networkConfiguration: {
                subnets: args.privateSubnets.map(subnet => subnet.id),
                securityGroups: [args.ecsSecurityGroup.id],
                assignPublicIp: false,
            },

            loadBalancers: [
                {
                    targetGroupArn: this.apiTargetGroup.arn,
                    containerName: `${name}-api`,
                    containerPort: 8000,
                },
            ],


            tags: {
                ...args.tags,
                Name: "happyrobot-api",
            },
        }, { parent: this });


        // Auto Scaling configuration
        this.createAutoScaling(args);

        // Register outputs
        this.registerOutputs({
            cluster: this.cluster,
            apiRepository: this.apiRepository,
            taskRole: this.taskRole,
            executionRole: this.executionRole,
            apiTaskDefinition: this.apiTaskDefinition,
            apiService: this.apiService,
            apiTargetGroup: this.apiTargetGroup,
        });
    }

    private createAutoScaling(args: ContainersArgs) {
        const name = "containers";
        // API Auto Scaling
        const apiAutoScalingTarget = new aws.appautoscaling.Target(`${name}-api-autoscaling-target`, {
            maxCapacity: 3,
            minCapacity: 1,
            resourceId: pulumi.interpolate`service/${this.cluster.name}/${this.apiService.name}`,
            scalableDimension: "ecs:service:DesiredCount",
            serviceNamespace: "ecs",
        }, { parent: this });

        new aws.appautoscaling.Policy(`${name}-api-autoscaling-policy`, {
            name: `${name}-api-cpu-autoscaling`,
            policyType: "TargetTrackingScaling",
            resourceId: apiAutoScalingTarget.resourceId,
            scalableDimension: apiAutoScalingTarget.scalableDimension,
            serviceNamespace: apiAutoScalingTarget.serviceNamespace,
            targetTrackingScalingPolicyConfiguration: {
                predefinedMetricSpecification: {
                    predefinedMetricType: "ECSServiceAverageCPUUtilization",
                },
                targetValue: 70,
                scaleInCooldown: 300,
                scaleOutCooldown: 300,
            },
        }, { parent: this });

    }
}
