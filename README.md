# sshtunnel-requests


## TODO

- [ ] 需要考虑清楚 `imoprt sshtunnel_requests`,
      `sshtunnel_requests.get(...)` 如何实现 ssh tunnel 参数比较合适，即如何使用这个库。
- [ ] 将 mdt 的 create tunnel 的实现 porting 过来
- [ ] 去除 register 进程销毁时，close connection 的实现方式，
      以弱引用缓存的方式实现。
      https://mp.weixin.qq.com/s/tGEyN2rKMVv8DbfQrhkbTg
- [ ] 参考sshtunnel的测试，加入httpbin用于测试。
- [ ] 必要情况下，参考requests的测试代码，增加不同情况的各种测试。


## 如何使用

要点：

1. 配置不应该写很多次：
    ```python
    import sshtunnel_requests
    resp = sshtunnel_requests.get(url, ...,
                                  ssh_host,
                                  ssh_port,
                                  ssh_...)
    resp_2 = sshtunnel_requests.get(url_2, ...,
                                    ssh_host,
                                    ssh_port,
                                    ssh_...)
   ```
   像这样写多次肯定是不理想的。

   **但是应该怎么实现和怎么使用呢？**
2. 应该允许一次性调用的写法：
    ```python
    import sshtunnel_requests
    resp = sshtunnel_requests.get(url, ...,
                                  ssh_host,
                                  ssh_port,
                                  ssh_...)
    # handler response, exit program
    ```
3. 肯定要允许通过配置文件读取ssh参数的默认情况，因为这个配置和mysql、redis、mongodb、等等这类配置的性质是相似的。

    和 mysql, redis, mongodb 这类配置性质相似，那么“这类配置”的惯用法是怎么样的呢？标准或通用习惯总结？

    1. 先参考类似 rabbimq、celery、SQLAlchemy 这类库，对于 quick-start 的【教程】/demo，里面对于这些的配置的使用
    2. 基于上面这一点，参考这些库内部是怎么实现这些配置

        要结合 connection 复用（缓存）以及建立新的connection的feature来学习。
    3. 这些库会默认读取某个路径(e.g. `~/.local/xxx.conf`) 的配置文件、环境变量、etc. 作为服务配置参数吗？
    4. 应当想到这个库概念上与SQLAlchemy相似，而不是Django相似；所以，flask-sqlalchemy是否提供了类似于 Django》settings.py 读取配置的能力呢？

       NOTE: 像flask-sqlalchemy作到 Django>settings.py 效果的feature，应当要想到，但不必急于实现；因为这种feature，在这个库的使用场景上，可能永远都用不上。
4. 考虑到 **3.** 这一点，可以考虑引入依赖注入技术

   https://python-dependency-injector.ets-labs.org/introduction/di_in_python.html


