import * as pulumi from "@pulumi/pulumi";
import * as aws from "@pulumi/aws";

export interface MonitoringArgs {
    ecsCluster: aws.ecs.Cluster;
    apiService: aws.ecs.Service;
    webService: aws.ecs.Service;
    database: aws.rds.Instance;
    loadBalancer: aws.lb.LoadBalancer;
    environment: string;
    tags: Record<string, string>;
}

export class MonitoringComponent extends pulumi.ComponentResource {
    public readonly apiLogGroup: aws.cloudwatch.LogGroup;
    public readonly webLogGroup: aws.cloudwatch.LogGroup;
    public readonly dashboard: aws.cloudwatch.Dashboard;
    public readonly dashboardUrl: pulumi.Output<string>;
    public readonly snsTopicAlerts: aws.sns.Topic;
    public readonly apiServiceAlarm: aws.cloudwatch.MetricAlarm;
    public readonly webServiceAlarm: aws.cloudwatch.MetricAlarm;
    public readonly databaseAlarm: aws.cloudwatch.MetricAlarm;
    public readonly albAlarm: aws.cloudwatch.MetricAlarm;

    constructor(name: string, args: MonitoringArgs, opts?: pulumi.ComponentResourceOptions) {
        super("happyrobot:monitoring", name, {}, opts);

        // Create CloudWatch Log Groups
        this.apiLogGroup = new aws.cloudwatch.LogGroup(`${name}-api-logs`, {
            name: `/aws/ecs/${name}-api`,
            retentionInDays: args.environment === "prod" ? 30 : 7,
            tags: {
                ...args.tags,
                Name: `${name}-api-logs`,
                Service: "api",
            },
        }, { parent: this });

        this.webLogGroup = new aws.cloudwatch.LogGroup(`${name}-web-logs`, {
            name: `/aws/ecs/${name}-web`,
            retentionInDays: args.environment === "prod" ? 30 : 7,
            tags: {
                ...args.tags,
                Name: `${name}-web-logs`,
                Service: "web",
            },
        }, { parent: this });

        // Create SNS topic for alerts
        this.snsTopicAlerts = new aws.sns.Topic(`${name}-alerts`, {
            name: `${name}-alerts`,
            displayName: "HappyRobot FDE Alerts",
            tags: {
                ...args.tags,
                Name: `${name}-alerts`,
            },
        }, { parent: this });

        // Create CloudWatch Alarms

        // API Service CPU Utilization Alarm
        this.apiServiceAlarm = new aws.cloudwatch.MetricAlarm(`${name}-api-cpu-alarm`, {
            name: `${name}-api-cpu-high`,
            description: "API service CPU utilization is too high",
            metricName: "CPUUtilization",
            namespace: "AWS/ECS",
            statistic: "Average",
            period: 300,
            evaluationPeriods: 2,
            threshold: 80,
            comparisonOperator: "GreaterThanThreshold",
            dimensions: {
                ServiceName: args.apiService.name,
                ClusterName: args.ecsCluster.name,
            },
            alarmActions: [this.snsTopicAlerts.arn],
            okActions: [this.snsTopicAlerts.arn],
            tags: {
                ...args.tags,
                Name: `${name}-api-cpu-alarm`,
                Service: "api",
            },
        }, { parent: this });

        // Web Service CPU Utilization Alarm
        this.webServiceAlarm = new aws.cloudwatch.MetricAlarm(`${name}-web-cpu-alarm`, {
            name: `${name}-web-cpu-high`,
            description: "Web service CPU utilization is too high",
            metricName: "CPUUtilization",
            namespace: "AWS/ECS",
            statistic: "Average",
            period: 300,
            evaluationPeriods: 2,
            threshold: 70,
            comparisonOperator: "GreaterThanThreshold",
            dimensions: {
                ServiceName: args.webService.name,
                ClusterName: args.ecsCluster.name,
            },
            alarmActions: [this.snsTopicAlerts.arn],
            okActions: [this.snsTopicAlerts.arn],
            tags: {
                ...args.tags,
                Name: `${name}-web-cpu-alarm`,
                Service: "web",
            },
        }, { parent: this });

        // Database CPU Utilization Alarm
        this.databaseAlarm = new aws.cloudwatch.MetricAlarm(`${name}-db-cpu-alarm`, {
            name: `${name}-db-cpu-high`,
            description: "Database CPU utilization is too high",
            metricName: "CPUUtilization",
            namespace: "AWS/RDS",
            statistic: "Average",
            period: 300,
            evaluationPeriods: 2,
            threshold: 80,
            comparisonOperator: "GreaterThanThreshold",
            dimensions: {
                DBInstanceIdentifier: args.database.identifier,
            },
            alarmActions: [this.snsTopicAlerts.arn],
            okActions: [this.snsTopicAlerts.arn],
            tags: {
                ...args.tags,
                Name: `${name}-db-cpu-alarm`,
                Service: "database",
            },
        }, { parent: this });

        // ALB Response Time Alarm
        this.albAlarm = new aws.cloudwatch.MetricAlarm(`${name}-alb-response-time-alarm`, {
            name: `${name}-alb-response-time-high`,
            description: "ALB response time is too high",
            metricName: "TargetResponseTime",
            namespace: "AWS/ApplicationELB",
            statistic: "Average",
            period: 300,
            evaluationPeriods: 2,
            threshold: 5, // 5 seconds
            comparisonOperator: "GreaterThanThreshold",
            dimensions: {
                LoadBalancer: args.loadBalancer.arnSuffix,
            },
            alarmActions: [this.snsTopicAlerts.arn],
            okActions: [this.snsTopicAlerts.arn],
            tags: {
                ...args.tags,
                Name: `${name}-alb-response-time-alarm`,
                Service: "loadbalancer",
            },
        }, { parent: this });

        // Create additional monitoring alarms
        this.createAdditionalAlarms(args);

        // Create CloudWatch Dashboard
        this.dashboard = new aws.cloudwatch.Dashboard(`${name}-dashboard`, {
            dashboardName: `HappyRobot-FDE-${args.environment}`,
            dashboardBody: pulumi.all([
                args.ecsCluster.name,
                args.apiService.name,
                args.webService.name,
                args.database.identifier,
                args.loadBalancer.arnSuffix,
            ]).apply(([clusterName, apiServiceName, webServiceName, dbIdentifier, albArn]) =>
                JSON.stringify({
                    widgets: [
                        {
                            type: "metric",
                            x: 0,
                            y: 0,
                            width: 12,
                            height: 6,
                            properties: {
                                metrics: [
                                    ["AWS/ECS", "CPUUtilization", "ServiceName", apiServiceName, "ClusterName", clusterName],
                                    [".", "MemoryUtilization", ".", ".", ".", "."],
                                ],
                                view: "timeSeries",
                                stacked: false,
                                region: aws.config.region!,
                                title: "API Service Metrics",
                                period: 300,
                                stat: "Average",
                            },
                        },
                        {
                            type: "metric",
                            x: 12,
                            y: 0,
                            width: 12,
                            height: 6,
                            properties: {
                                metrics: [
                                    ["AWS/ECS", "CPUUtilization", "ServiceName", webServiceName, "ClusterName", clusterName],
                                    [".", "MemoryUtilization", ".", ".", ".", "."],
                                ],
                                view: "timeSeries",
                                stacked: false,
                                region: aws.config.region!,
                                title: "Web Service Metrics",
                                period: 300,
                                stat: "Average",
                            },
                        },
                        {
                            type: "metric",
                            x: 0,
                            y: 6,
                            width: 12,
                            height: 6,
                            properties: {
                                metrics: [
                                    ["AWS/RDS", "CPUUtilization", "DBInstanceIdentifier", dbIdentifier],
                                    [".", "DatabaseConnections", ".", "."],
                                    [".", "ReadLatency", ".", "."],
                                    [".", "WriteLatency", ".", "."],
                                ],
                                view: "timeSeries",
                                stacked: false,
                                region: aws.config.region!,
                                title: "Database Metrics",
                                period: 300,
                                stat: "Average",
                            },
                        },
                        {
                            type: "metric",
                            x: 12,
                            y: 6,
                            width: 12,
                            height: 6,
                            properties: {
                                metrics: [
                                    ["AWS/ApplicationELB", "RequestCount", "LoadBalancer", albArn],
                                    [".", "TargetResponseTime", ".", "."],
                                    [".", "HTTPCode_Target_2XX_Count", ".", "."],
                                    [".", "HTTPCode_Target_4XX_Count", ".", "."],
                                    [".", "HTTPCode_Target_5XX_Count", ".", "."],
                                ],
                                view: "timeSeries",
                                stacked: false,
                                region: aws.config.region!,
                                title: "Load Balancer Metrics",
                                period: 300,
                                stat: "Sum",
                            },
                        },
                        {
                            type: "log",
                            x: 0,
                            y: 12,
                            width: 24,
                            height: 6,
                            properties: {
                                query: `SOURCE '${this.apiLogGroup.name}'\n| fields @timestamp, @message\n| filter @message like /ERROR/\n| sort @timestamp desc\n| limit 100`,
                                region: aws.config.region!,
                                title: "Recent API Errors",
                                view: "table",
                            },
                        },
                        {
                            type: "metric",
                            x: 0,
                            y: 18,
                            width: 8,
                            height: 6,
                            properties: {
                                metrics: [
                                    ["AWS/ECS", "RunningTaskCount", "ServiceName", apiServiceName, "ClusterName", clusterName],
                                ],
                                view: "singleValue",
                                region: aws.config.region!,
                                title: "API Running Tasks",
                                period: 300,
                                stat: "Average",
                            },
                        },
                        {
                            type: "metric",
                            x: 8,
                            y: 18,
                            width: 8,
                            height: 6,
                            properties: {
                                metrics: [
                                    ["AWS/ECS", "RunningTaskCount", "ServiceName", webServiceName, "ClusterName", clusterName],
                                ],
                                view: "singleValue",
                                region: aws.config.region!,
                                title: "Web Running Tasks",
                                period: 300,
                                stat: "Average",
                            },
                        },
                        {
                            type: "metric",
                            x: 16,
                            y: 18,
                            width: 8,
                            height: 6,
                            properties: {
                                metrics: [
                                    ["AWS/RDS", "DatabaseConnections", "DBInstanceIdentifier", dbIdentifier],
                                ],
                                view: "singleValue",
                                region: aws.config.region!,
                                title: "Database Connections",
                                period: 300,
                                stat: "Average",
                            },
                        },
                    ],
                })
            ),
        }, { parent: this });

        // Generate dashboard URL
        this.dashboardUrl = pulumi.interpolate`https://${aws.config.region}.console.aws.amazon.com/cloudwatch/home?region=${aws.config.region}#dashboards:name=${this.dashboard.dashboardName}`;

        // Register outputs
        this.registerOutputs({
            apiLogGroup: this.apiLogGroup,
            webLogGroup: this.webLogGroup,
            dashboard: this.dashboard,
            dashboardUrl: this.dashboardUrl,
            snsTopicAlerts: this.snsTopicAlerts,
            apiServiceAlarm: this.apiServiceAlarm,
            webServiceAlarm: this.webServiceAlarm,
            databaseAlarm: this.databaseAlarm,
            albAlarm: this.albAlarm,
        });
    }

    private createAdditionalAlarms(args: MonitoringArgs) {
        // Database Connection Count Alarm
        new aws.cloudwatch.MetricAlarm(`${this.getResource().urn.name}-db-connections-alarm`, {
            name: `${this.getResource().urn.name}-db-connections-high`,
            description: "Database connection count is too high",
            metricName: "DatabaseConnections",
            namespace: "AWS/RDS",
            statistic: "Average",
            period: 300,
            evaluationPeriods: 2,
            threshold: 180, // Close to max_connections (200)
            comparisonOperator: "GreaterThanThreshold",
            dimensions: {
                DBInstanceIdentifier: args.database.identifier,
            },
            alarmActions: [this.snsTopicAlerts.arn],
            okActions: [this.snsTopicAlerts.arn],
            tags: {
                ...args.tags,
                Name: `${this.getResource().urn.name}-db-connections-alarm`,
                Service: "database",
            },
        }, { parent: this });

        // ALB Target Health Alarm
        new aws.cloudwatch.MetricAlarm(`${this.getResource().urn.name}-alb-unhealthy-targets-alarm`, {
            name: `${this.getResource().urn.name}-alb-unhealthy-targets`,
            description: "ALB has unhealthy targets",
            metricName: "UnHealthyHostCount",
            namespace: "AWS/ApplicationELB",
            statistic: "Average",
            period: 60,
            evaluationPeriods: 2,
            threshold: 0,
            comparisonOperator: "GreaterThanThreshold",
            dimensions: {
                LoadBalancer: args.loadBalancer.arnSuffix,
            },
            alarmActions: [this.snsTopicAlerts.arn],
            okActions: [this.snsTopicAlerts.arn],
            tags: {
                ...args.tags,
                Name: `${this.getResource().urn.name}-alb-unhealthy-targets-alarm`,
                Service: "loadbalancer",
            },
        }, { parent: this });

        // ECS Service Desired vs Running Task Count Alarm
        new aws.cloudwatch.MetricAlarm(`${this.getResource().urn.name}-api-task-count-alarm`, {
            name: `${this.getResource().urn.name}-api-task-count-low`,
            description: "API service running task count is below desired",
            metricName: "RunningTaskCount",
            namespace: "AWS/ECS",
            statistic: "Average",
            period: 300,
            evaluationPeriods: 2,
            threshold: 1, // Should have at least 1 running task
            comparisonOperator: "LessThanThreshold",
            dimensions: {
                ServiceName: args.apiService.name,
                ClusterName: args.ecsCluster.name,
            },
            alarmActions: [this.snsTopicAlerts.arn],
            okActions: [this.snsTopicAlerts.arn],
            tags: {
                ...args.tags,
                Name: `${this.getResource().urn.name}-api-task-count-alarm`,
                Service: "api",
            },
        }, { parent: this });

        // High Error Rate Alarm (5XX responses)
        new aws.cloudwatch.MetricAlarm(`${this.getResource().urn.name}-alb-5xx-alarm`, {
            name: `${this.getResource().urn.name}-alb-5xx-high`,
            description: "High rate of 5XX errors from ALB",
            metricName: "HTTPCode_Target_5XX_Count",
            namespace: "AWS/ApplicationELB",
            statistic: "Sum",
            period: 300,
            evaluationPeriods: 2,
            threshold: 10, // More than 10 5XX errors in 5 minutes
            comparisonOperator: "GreaterThanThreshold",
            dimensions: {
                LoadBalancer: args.loadBalancer.arnSuffix,
            },
            alarmActions: [this.snsTopicAlerts.arn],
            okActions: [this.snsTopicAlerts.arn],
            treatMissingData: "notBreaching",
            tags: {
                ...args.tags,
                Name: `${this.getResource().urn.name}-alb-5xx-alarm`,
                Service: "loadbalancer",
            },
        }, { parent: this });
    }
}
