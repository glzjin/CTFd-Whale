# Changelog

## 2019-10-30

- Optimize for multi worker.
- Try to fix concurrency request problem.

Now You should set the redis with REDIS_HOST environment varible.

## 2019-09-26

- Add frp http port setting.

You should config it at the settings for http redirect.

## 2019-09-15

- Add Container Network Setting and DNS Setting.

Now You can setup a DNS Server in your Container Network.
- For single-instance network, Just connect your dns server to it and input the ip address in the seeting panel.
- For multi-instance network, You should rename the dns server to a name include "dns", than add it to auto connect instance. It will be used as a dns server.

## 2019-09-14

- Refine plugin path.

## 2019-09-13

- Refine removal.

## 2019-08-29

- Add CPU usage limit.
- Allow the multi-image challenge.

Upgrade:
1. Execute this SQL in ctfd database.

```
alter table dynamic_docker_challenge add column cpu_limit float default 0.5 after memory_limit;
```  

2. Setting the containers you want to plugin to a single multi-image network. (In settings panel)

3. When you create a challenge you can set the docker image like this

```
{"socks": "serjs/go-socks5-proxy", "web": "blog_revenge_blog", "mysql": "blog_revenge_mysql", "oauth": "blog_revenge_oauth"}
```

The first one will be redirected the traffic.
