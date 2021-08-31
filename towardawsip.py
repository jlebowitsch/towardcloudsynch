import boto3
import botocore
import json
import concurrent.futures


profile='default'
threadcount=10
awsapis={
    "ec2":["describe_addresses()"],
    "s3":["list_buckets()"],
    "elasticbeanstalk":["describe_environments()"],
    "route53":["list_hosted_zones()"],
    "cloudfront":[]
}

apisubcalls={
    "list_buckets()":{
        "get_bucket_website()":"getbucketwebsite"
    },
    "list_hosted_zones()":{
        "list_resource_record_sets()":"ListResourceRecordSets"
    }
     
}

def clientregions(client):
    if client=='ec2':
        sess = boto3.session.Session(profile_name=profile)
        ec2=sess.client("ec2")
        try:
            regions=[x['RegionName'] for x in ec2.describe_regions()['Regions']] #requires ec2
            return regions
        except  botocore.exceptions.ClientError as error:
            return format(error)
    else:
        return ["us-east-1"]


def listservice(client, region):
    sess = boto3.session.Session(profile_name=profile)
    ecx=sess.client(client, region_name=region)
    response={}
    for api in awsapis[client]:
        func="ecx."+api
        try:
            response[api]=eval(func)             
        except  botocore.exceptions.ClientError as error:
            response[api]=format(error)
        if api in apisubcalls.keys():
                for subapi, apifunc in apisubcalls[api].items(): 
                    response[subapi]=globals()[apifunc](response[api],ecx)   
    return response

def getbucketwebsite(rawbucketlist,client):
    
    Z=[x['Name'] for x in rawbucketlist['Buckets']]
    W={}
    for z in Z:
        try:
            W[z]=client.get_bucket_website(Bucket=z)
        except botocore.exceptions.ClientError as error:
            W[z]=format(error)
    return W

def ListResourceRecordSets(rawbucketlist,client):
    Z=[x['Id'] for x in rawbucketlist['HostedZones']]
    W={}
    for z in Z:
        try:
            W[z]=client.list_resource_record_sets(HostedZoneId=z)
        except botocore.exceptions.ClientError as error:
            W[z]=format(error)
    return W
            
def main():
    ZZ={x:{} for x in awsapis.keys()}
    with concurrent.futures.ThreadPoolExecutor(max_workers=threadcount) as executor:
               future_to_fq = {executor.submit(listservice, client, region): [client,region] for client in awsapis.keys() for region in clientregions(client)}
               for future in concurrent.futures.as_completed(future_to_fq):
                   cr = future_to_fq[future]
                   ZZ[cr[0]][cr[1]]=future.result()
    return ZZ


RRR=main()
    
for reg in RRR['s3']:
    newbuck=[]
    for buc in RRR['s3'][reg]['list_buckets()']['Buckets']:
        buc['CreationDate']=buc['CreationDate'].isoformat()
        newbuck.append(buc)
    RRR['s3'][reg]['list_buckets()']['Buckets']=newbuck
print(json.dumps(RRR, sort_keys=True, indent=4))
with open('cyberpion.json','w', encoding='utf-8') as f:
    json.dump(RRR, f, ensure_ascii=False, indent=4)
