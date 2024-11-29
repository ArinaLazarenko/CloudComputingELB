#!/bin/bash

apt-get update;
apt-get install python3 python3-pip -y;
pip3 install fastapi uvicorn --break-system-packages;
instanceId=$(ec2metadata --instance-id);

python3 -c "
from fastapi import FastAPI
import uvicorn
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI()


@app.get('/')
async def root():
    return {'Instance has received the request': '$instanceId'}

@app.get('/cluster1')
async def cluster1():
    return {'Cluster1 has received the request on Instance: ': '$instanceId'}

@app.get('/cluster2')
async def cluster2():
    return {'Cluster2 has received the request on instance: ': '$instanceId'}


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
";