import fcntl
import os
import asyncio


class asyncfile:
    BLOCK_SIZE = 512

    def __init__(self, filename, mode, loop=None):
        self.fd = open(filename, mode=mode)
        # 增加文件的某个flags，比如文件是阻塞的，想设置成非阻塞:
        flag = fcntl.fcntl(self.fd, fcntl.F_GETFL)
        if fcntl.fcntl(self.fd, fcntl.F_SETFL, flag | os.O_NONBLOCK) != 0:
            raise OSError()

        if loop is None:
            loop = asyncio.get_event_loop()
        self.loop = loop
        # bytearray方法返回一个新字节数组。这个数组里的元素是可变的，并且每个元素的值范围: 0 <= x < 256。
        self.rbuffer = bytearray()

    def read_step(self, future, n, total):
        # read()方法用于从文件读取指定的字节数，如果未给定或为负则读取所有。
        res = self.fd.read(n)

        if res is None:
            self.loop.call_soon(self.read_step, future, n, total)
            return
        if not res:  # EOF
            future.set_result(bytes(self.rbuffer))
            return

        self.rbuffer.extend(res)

        if total > 0:
            left = total - len(self.rbuffer)
            print(left)
            if left <= 0:
                # res, self.rbuffer = self.rbuffer[:n], self.rbuffer[n:]
                future.set_result(bytes(self.rbuffer))
            else:
                left = min(self.BLOCK_SIZE, left)
                self.loop.call_soon(self.read_step, future, left, total)
        else:
            self.loop.call_soon(self.read_step, future, self.BLOCK_SIZE, total)

    def read(self, n=-1):
        # Future:主要用来保存任务的状态,负责终止loop的循环
        future = asyncio.Future(loop=self.loop)

        if n == 0:
            # 设置任务的结果，必须在result()之前执行，否则报错
            future.set_result(b"")
            return future
        elif n < 0:
            self.rbuffer.clear()
            self.loop.call_soon(self.read_step, future, self.BLOCK_SIZE, n)
        else:
            self.rbuffer.clear()
            # 设置回调函数
            self.loop.call_soon(self.read_step, future, min(self.BLOCK_SIZE, n), n)

        return future


async def foo():
    path = "./[图灵原创].算法的乐趣.revise7.pdf"
    af = asyncfile("./[图灵原创].算法的乐趣.revise7.pdf", mode="rb")
    total_size = os.path.getsize(path)
    content = await af.read(total_size)
    print(content)


# 同步读
def bar():
    with open(f"./[图灵原创].算法的乐趣.revise7.pdf", "rb") as f:
        f.read()


if __name__ == "__main__":
    tasks = [foo()]
    # get_event_loop
    # 获取当前事件循环。
    # 如果当前 OS 线程没有设置当前事件循环，该 OS 线程为主线程，
    # 并且 set_event_loop() 还没有被调用，则 asyncio 将创建一个新的事件循环并将其设为当前事件循环。

    # run_until_complete 运行直到 future ( Future 的实例 ) 被完成。
    # 如果参数是 coroutine object ，将被隐式调度为 asyncio.Task 来运行。
    # 返回 Future 的结果 或者引发相关异常。

    # asyncio.wait
    # 并发地运行可迭代对象中的携程对象进入阻塞状态直到满足 return_when 所指定的条件。
    asyncio.get_event_loop().run_until_complete(asyncio.wait(tasks))
