# DS course  
# Project 2  
# Simple Distributed File System 

All storages and name server supposed to be in a single LAN.  
Client has to be exposed to the open network.  


## How to start:  
Storage:  
```
docker run -it -p 3504-3600:3504-3600 r0ach20/dfs_storage_server
```
Name:  
```
docker run -it -p 6235:6235 r0ach20/dfs_name_server
```
Only one storage could be deployed on a single machine.  
After starting system is ready to use, and clients can connect to the name server.  
Client:  
```
docker run -it -p 3504-3600:3504-3600 r0ach20/dfs_client (ip address of the name server)
```
or
```
python3 client.py (ip address of the name server)
```

## Architectural diagram
![diag](https://github.com/validolchik/ds_project2/blob/main/images/DS2.png)

## Protocols  
# Read and write  

# Storage discover and synchronization  

# Everything else
Every other message inthe system follows simple `type][arg1][arg2][padding` sturcture followed by the response `type][body_length][body'
