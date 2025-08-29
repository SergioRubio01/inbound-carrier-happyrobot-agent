import * as pulumi from "@pulumi/pulumi";
import * as aws from "@pulumi/aws";
import { NetworkingComponent } from "./components/networking";
import { DatabaseComponent } from "./components/database";
import { ContainersComponent } from "./components/containers";
import { LoadBalancerComponent } from "./components/loadbalancer";
import { MonitoringComponent } from "./components/monitoring";
import { HappyRobotDNS } from "./components/route53";
import { IAMComponent } from "./components/iam";

// Get configuration
const config = new pulumi.Config();
const environment = config.get("environment") || "dev";
const projectName = "happyrobot-fde";
const resourcePrefix = `happyrobot-${environment}`; // Prefix for all resources

// Business logic configuration (passed to containers component)
// These are configured in Pulumi.happyrobot-fde.yaml:
// - maxLoadWeightLbs: Maximum weight for loads in pounds (default: 80000)
// - maxReferenceNumberCounter: Maximum counter for reference numbers (default: 99999)
// - maxRateAmount: Maximum rate amount in dollars (default: 999999.99)

// Common tags for all resources
const commonTags = {
    Project: projectName,
    Environment: environment,
    ManagedBy: "pulumi",
    Owner: "engineering",
};

// Create IAM policies for deployment permissions
// This includes Route 53 permissions needed for DNS management
// The IAM user is configured in Pulumi.happyrobot-fde.yaml
const deploymentIamUser = config.get("deploymentIamUser");
const iam = new IAMComponent(`${resourcePrefix}-iam`, {
    environment,
    tags: commonTags,
    attachToUser: deploymentIamUser, // Attach policies to the CI/CD user if configured
});

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
// Component name: happyrobot-{environment}-containers
// This will create ECR repository: happyrobot-{environment}-containers-api
// Must match ECR_API_REPOSITORY in GitHub workflow (.github/workflows/deploy.yml)
const containers = new ContainersComponent(`${resourcePrefix}-containers`, {
    vpc: networking.vpc,
    privateSubnets: networking.privateSubnets,
    ecsSecurityGroup: networking.ecsSecurityGroup,
    databaseEndpoint: database.endpoint,
    databaseSecretArn: database.secretArn,
    environment,
    apiKey: config.require("apiKey"),
    enableHttps: config.getBoolean("enableHttps") || false, // Pass HTTPS config to containers
    tags: commonTags,
});

// Create Application Load Balancer
const loadBalancer = new LoadBalancerComponent(`${resourcePrefix}-loadbalancer`, {
    vpc: networking.vpc,
    publicSubnets: networking.publicSubnets,
    albSecurityGroup: networking.albSecurityGroup,
    apiTargetGroup: containers.apiTargetGroup,
    certificateArn: config.get("certificateArn"), // Optional SSL certificate for custom domains
    enableHttps: config.getBoolean("enableHttps") || false, // Enable HTTPS support
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

// Create Route 53 DNS records for api.bizai.es
// IMPORTANT: This depends on IAM being set up first to avoid permission errors
const dns = new HappyRobotDNS(`${resourcePrefix}-dns`, {
    albDnsName: loadBalancer.alb.dnsName,
    albZoneId: loadBalancer.alb.zoneId,
    domainName: "api.bizai.es",
    environment,
    commonTags,
}, { dependsOn: [iam] }); // Ensure IAM is created first

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
export const apiDomainName = dns.apiRecord.fqdn;

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
    dns: {
        apiDomain: dns.apiRecord.fqdn,
        apiUrl: pulumi.interpolate`https://${dns.apiRecord.fqdn}`,
    },
    monitoring: {
        dashboardUrl: monitoring.dashboardUrl,
        logGroupNames: {
            api: monitoring.apiLogGroup.name,
        },
    },
    iam: {
        policyAttached: !!iam.comprehensiveDeploymentPolicy,
        note: "Comprehensive inline policy attached directly to the specified IAM user",
    },
};
