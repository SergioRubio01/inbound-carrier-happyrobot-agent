import * as pulumi from "@pulumi/pulumi";
import * as aws from "@pulumi/aws";
import { NetworkingComponent } from "./components/networking";
import { DatabaseComponent } from "./components/database";
import { ContainersComponent } from "./components/containers";
import { LoadBalancerComponent } from "./components/loadbalancer";
import { MonitoringComponent } from "./components/monitoring";

// Get configuration
const config = new pulumi.Config();
const environment = config.get("environment") || "dev";
const projectName = "happyrobot-fde";
const resourcePrefix = `happyrobot-${environment}`; // Prefix for all resources

// Common tags for all resources
const commonTags = {
    Project: projectName,
    Environment: environment,
    ManagedBy: "pulumi",
    Owner: "engineering",
};

// Create VPC and networking infrastructure
const networking = new NetworkingComponent(`${resourcePrefix}-networking`, {
    cidrBlock: "10.0.0.0/16",
    availabilityZones: 2,
    environment,
    tags: commonTags,
});

// Create RDS PostgreSQL database
const database = new DatabaseComponent(`${resourcePrefix}-database`, {
    vpc: networking.vpc,
    privateSubnets: networking.privateSubnets,
    databaseSecurityGroup: networking.databaseSecurityGroup,
    instanceClass: config.get("dbInstanceClass") || "db.t3.micro",
    allocatedStorage: parseInt(config.get("dbAllocatedStorage") || "20"),
    environment,
    tags: commonTags,
});

// Create ECS cluster and container services
const containers = new ContainersComponent(`${resourcePrefix}-containers`, {
    vpc: networking.vpc,
    privateSubnets: networking.privateSubnets,
    ecsSecurityGroup: networking.ecsSecurityGroup,
    databaseEndpoint: database.endpoint,
    databaseSecretArn: database.secretArn,
    environment,
    tags: commonTags,
});

// Create Application Load Balancer
const loadBalancer = new LoadBalancerComponent(`${resourcePrefix}-loadbalancer`, {
    vpc: networking.vpc,
    publicSubnets: networking.publicSubnets,
    albSecurityGroup: networking.albSecurityGroup,
    apiTargetGroup: containers.apiTargetGroup,
    certificateArn: config.get("certificateArn"), // Optional SSL certificate
    environment,
    tags: commonTags,
});

// Create monitoring and logging
const monitoring = new MonitoringComponent(`${resourcePrefix}-monitoring`, {
    ecsCluster: containers.cluster,
    apiService: containers.apiService,
    database: database.instance,
    loadBalancer: loadBalancer.alb,
    environment,
    tags: commonTags,
});

// Export important values
export const vpcId = networking.vpc.id;
export const publicSubnetIds = networking.publicSubnets.map(subnet => subnet.id);
export const privateSubnetIds = networking.privateSubnets.map(subnet => subnet.id);
export const databaseEndpoint = database.endpoint;
export const ecsClusterName = containers.cluster.name;
export const apiRepositoryUrl = containers.apiRepository.repositoryUrl;
export const loadBalancerDnsName = loadBalancer.alb.dnsName;
export const loadBalancerZoneId = loadBalancer.alb.zoneId;
export const dashboardUrl = monitoring.dashboardUrl;

// Export environment-specific outputs
export const outputs = {
    vpc: {
        id: networking.vpc.id,
        cidrBlock: networking.vpc.cidrBlock,
    },
    database: {
        endpoint: database.endpoint,
        port: database.port,
        secretArn: database.secretArn,
    },
    cluster: {
        name: containers.cluster.name,
        arn: containers.cluster.arn,
    },
    repositories: {
        api: containers.apiRepository.repositoryUrl,
    },
    loadBalancer: {
        dnsName: loadBalancer.alb.dnsName,
        hostedZoneId: loadBalancer.alb.zoneId,
        apiTargetGroupArn: containers.apiTargetGroup.arn,
    },
    monitoring: {
        dashboardUrl: monitoring.dashboardUrl,
        logGroupNames: {
            api: monitoring.apiLogGroup.name,
        },
    },
};
