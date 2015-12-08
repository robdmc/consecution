from unittest import TestCase
import asyncio

from consecution.nodes import ManualProducerNode, ComputeNode

class SimpleTest(TestCase):
    def test_producer(self):
        producer = ManualProducerNode()
        computer = ComputeNode(upstream=producer)

        #async def start_computer():
        #    computer.start()


        master = asyncio.gather(
            asyncio.ensure_future(computer.start()),
            asyncio.ensure_future(producer.produce_from(range(10))),
        )


        loop = asyncio.get_event_loop()
        loop.run_until_complete(master)
        print()
        print('done')
    #def test_nothing(self):
    #    async def runner():
    #        print('hello')

    #    #loop = asyncio.new_event_loop()
    #    loop = asyncio.get_event_loop()
    #    loop.run_until_complete(runner())

    #def test_nothing2(self):
    #    async def dummy():
    #        print('starting sleep 2')
    #        await asyncio.sleep(1)
    #        print('finishing sleep 2')
    #    print()
    #    print('testing nothing 2')
    #    print('done testing 2')

    #    #loop = asyncio.new_event_loop()
    #    loop = asyncio.get_event_loop()
    #    loop.run_until_complete(dummy())


    #loop = asyncio.get_event_loop()
    #loop.run_until_complete(main())
    #loop.close()

