# CTFd-Whale

能够支持题目容器化部署的CTFd插件

## 功能

- 利用`frp`与`docker swarm`做到多容器部署
- web题目支持利用frp的subdomain实现每个用户单独的域名访问
- 参赛选手一键启动题目环境，支持容器续期
- 自动生成随机flag，并通过环境变量传入容器
- 管理员可以在后台查看启动的容器
- 支持自定义flag生成方式与web题目子域名生成方式

## 使用方式

请参考[INSTALL.zh-cn.md](INSTALL.zh-cn.md)

## Demo

[BUUCTF](https://buuoj.cn)

## 第三方使用说明

- [CTFd-Whale 推荐部署实践](https://www.zhaoj.in/read-6333.html)
- [手把手教你如何建立一个支持ctf动态独立靶机的靶场（ctfd+ctfd-whale)](https://blog.csdn.net/fjh1997/article/details/100850756)

## 使用案例

![](https://www.zhaoj.in/wp-content/uploads/2019/08/1565947849bb2f3ed7912fb85afbbf3e6135cb89ca.png)

![](https://www.zhaoj.in/wp-content/uploads/2019/08/15659478989e90e7a3437b1bdd5b9e617d7071a79f.png)

![](https://www.zhaoj.in/wp-content/uploads/2019/08/15659479342f5f6d33e2eeaedb313facd77b2bbccb.png)

![](https://www.zhaoj.in/wp-content/uploads/2019/08/1565923903609e6c236759a5663be8e0fb57904482.png)

## 友情链接

- [CTFd-Owl](https://github.com/D0g3-Lab/H1ve/tree/master/CTFd/plugins/ctfd-owl) (支持部署compose)
