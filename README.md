# CTFd-Whale
A plugin for CTFd which allow your users to launch a standalone instance for challenges.

![https://www.zhaoj.in/wp-content/uploads/2019/08/1565947849bb2f3ed7912fb85afbbf3e6135cb89ca.png](https://www.zhaoj.in/wp-content/uploads/2019/08/1565947849bb2f3ed7912fb85afbbf3e6135cb89ca.png)

![https://www.zhaoj.in/wp-content/uploads/2019/08/15659478989e90e7a3437b1bdd5b9e617d7071a79f.png](https://www.zhaoj.in/wp-content/uploads/2019/08/15659478989e90e7a3437b1bdd5b9e617d7071a79f.png)

![https://www.zhaoj.in/wp-content/uploads/2019/08/15659479342f5f6d33e2eeaedb313facd77b2bbccb.png](https://www.zhaoj.in/wp-content/uploads/2019/08/15659479342f5f6d33e2eeaedb313facd77b2bbccb.png)

![https://www.zhaoj.in/wp-content/uploads/2019/08/1565923903609e6c236759a5663be8e0fb57904482.png](https://www.zhaoj.in/wp-content/uploads/2019/08/1565923903609e6c236759a5663be8e0fb57904482.png)

## Features
- Provide a new challenge type - dynamic_docker.
- The player can launch an instance for these challenge on the challenge board by one click.
- Every instance has a unique flag.
- Admin can manage the instance at the admin panel.

## Usage
0. You should init docker swarm, and add your node to it. And name them with following command:

```
docker node update --label-add name=windows-1 ****
docker node update --label-add name=linux-1 ****
```

Name of them should begin with windows- or linux-.

1. Copy this folder to your ctfd plugins folder. *Make sure the folder name is 'ctfd-whale'.*
2. Deploy [frp](https://github.com/fatedier/frp/) on your servers, and you should make sure CTFd can access frpc admin API directly.
3. And also make sure docker API is accessible to CTFd, you should create a network in docker called 'ctfd_frp-containers' which allow frp redirect traffic to challenge instances.
4. Configure this plugin on the admin panel.
5. Now you may create a challenge, choose the challenge type - dynamic_docker and fill the form.
6. Click the preview button, then you can launch an instance for this challenge.
7. Enjoy it:)

## Some configuration file

1. docker-compose.yml for CTFd I used.

```
version: '2.2'

services:
  ctfd-nginx:
    build: ./nginx
    user: root
    restart: always
    ports:
      - "80:80"
      - "443:443"
    networks:
        default:
        internal:
    depends_on:
      - ctfd
    cpus: '2.50'
    mem_limit: 150M
  ctfd:
    build: .
    user: root
    restart: always
    environment:
      - UPLOAD_FOLDER=/var/uploads
      - DATABASE_URL=mysql+pymysql://root:ctfd@db/ctfd
      - REDIS_URL=redis://cache:6379
      - WORKERS=1
      - LOG_FOLDER=/var/log/CTFd
      - ACCESS_LOG=-
      - ERROR_LOG=-
      - REVERSE_PROXY=true
    volumes:
      - .data/CTFd/logs:/var/log/CTFd
      - .data/CTFd/uploads:/var/uploads
      - .:/opt/CTFd:ro
      - /var/run/docker.sock:/var/run/docker.sock
    depends_on:
      - db
    networks:
        default:
        internal:
        frp:
            ipv4_address: 172.1.0.2
    cpus: '2.50'
    mem_limit: 450M

  db:
    image: mariadb:10.4
    restart: always
    environment:
      - MYSQL_ROOT_PASSWORD=ctfd
      - MYSQL_USER=ctfd
      - MYSQL_PASSWORD=ctfd
    volumes:
      - .data/mysql:/var/lib/mysql
    networks:
        internal:
    # This command is required to set important mariadb defaults
    command: [mysqld, --character-set-server=utf8mb4, --collation-server=utf8mb4_unicode_ci, --wait_timeout=28800, --log-warnings=0]
    cpus: '2.50'
    mem_limit: 750M

  cache:
    image: redis:4
    restart: always
    volumes:
      - .data/redis:/data
    networks:
        internal:
    cpus: '2.50'
    mem_limit: 450M

  frpc:
    image: glzjin/frp:latest
    restart: always
    volumes:
      - ./frpc:/conf/
    entrypoint:
        - /usr/local/bin/frpc
        - -c
        - /conf/frpc.ini
    networks:
        frp:
            ipv4_address: 172.1.0.3
        frp-containers:
    cpus: '1.50'
    mem_limit: 250M

networks:
    default:
    internal:
        internal: true
    frp:
        driver: bridge
        ipam:
            config:
                - subnet: 172.1.0.0/16
    frp-containers:
        driver: overlay
        internal: true
        ipam:
            config:
                - subnet: 172.2.0.0/16
```

Internet --> frps1 --> frpc1 --> nginx --> ctfd

Internet --> frps2 --> frps2 --> chanllenge_instance

2. frpc config tamplate

```
[common]
token = ***************
server_addr = *******
server_port = ****
pool_count = 200
tls_enable = true

# Make sure it's only exposed the port to the network that only has ctfd and frp, not the frp and challenge instance one.
admin_addr = 172.1.0.3
admin_port = 7400
```

3. Some challenge image you can use.

[https://github.com/CTFTraining/CTFTraining](https://github.com/CTFTraining/CTFTraining)

4. Challenge image requirement
- Support set flag by setting docker environment "FLAG".

5. The configuration I have set on the CTFd admin panel.
![https://www.zhaoj.in/wp-content/uploads/2019/08/1565931400faa3a335e9a8531e8e34cdb1e5ede899.png](https://www.zhaoj.in/wp-content/uploads/2019/08/1565931400faa3a335e9a8531e8e34cdb1e5ede899.png)

## Demo
[BUUCTF](https://buuoj.cn)

## Third-Party Introduction
- [CTFd-Whale 推荐部署实践](https://www.zhaoj.in/read-6333.html)
- [手把手教你如何建立一个支持ctf动态独立靶机的靶场（ctfd+ctfd-whale)](https://blog.csdn.net/fjh1997/article/details/100850756)

## Twins

- [CTFd-Owl](https://raw.githubusercontent.com/D0g3-Lab/H1ve/master/CTFd/plugins/ctfd-owl) (Support docker-compose)
