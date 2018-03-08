import os
import rpyc
import pickle
from reply import Reply

NN_IP = ''
PORT = ''
MY_IP = ''

class DataNodeService(rpyc.Service):
    class exposed_BlockStore:
        def __init__(self, file_name = 'persistent.dat'):
            self.block_id = set()
            self.name_map = file_name
            self.load_node()

        #load data node if previously started
        def load_node(self):
            print('Loading previous storage')
            try:
                with open(self.name_map, 'rb') as f:
                    while True:
                        try:
                            self.block_id.add(pickle.load(f))
                        except EOFError:
                            break
            except:
                print('Could not load persistent data, creating new')
                self.block_id = set()

        #write block to block report
        def save_block(self, id):
            print('saving ', id)
            with open(self.name_map, 'a+b') as f:
                pickle.dump(id, f)
            f.close()
            self.block_id.add(id)
            print('block report is', self.block_id)

        def block_report(self):
            blocks = []
            with open(self.name_map, 'rb') as f:
                while 1:
                    try:
                        blocks.append(pickle.load(f))
                    except EOFError:
                        break
            print('printing block report')
            print(blocks)
            f.close()
            return blocks

        #save block to storage from client request
        def exposed_put_block(self, file_name, data):
            print('new file name', file_name)
            if file_name in self.block_id:
                return Reply.error('File name already exists')
            #this is not right
            else:
                try:
                    with open(file_name, 'wb') as f:
                        f.write(data)
                except:
                    self.block_id.remove(id)
                    return Reply.error('Error saving block')

                self.save_block(file_name)
                return Reply.reply()
            #also need to replicate the block to other datanodes

        def exposed_get_block(self, file_name):
            if file_name in self.block_id:
                with open(file_name, 'rb') as f:
                    pickle.load(f)
                return Reply.reply(f)
            else:
                return Reply.error('File not found')


        #delete a block
        def exposed_delete_block(self, id):
            if id in self.block_id:
                self.block_id.remove(id)
                return Reply.reply()
            else:
                return Reply.error('Block not found')

        # Precondition:
        # Postcondition: block report is sent
        # Function: sends updates on what is being stored on the DataNode
        def send_block_report(self, ip, path):
            dir = os.listdir(path)
            block_list = []
            for path, dirs, files in os.walk(path):
                for filename in files:
                    block_list.append(filename)
            c = rpyc.connect(NN_IP, PORT)
            cmds = c.root.receive_block_report(MY_IP, block_list)


    # Precondition: request to delete a block is recvd from client
    # Postcondition: block is removed from storage, and confirmation is sent
    # Function:
    def exposed_deleteBlock(self, path):
        pass

    # Precondition: a block is received from another DataNode
    # Postcondition: a block is forwarded to the next DataNode in the path
    # Function:
    def exposed_replicateBlock(self, file, path, destinations):
        self.storeBlock(file, path)
        destinations = destinations[1:]
        if len(destinations) > 0:
            c = rpyc.connect(destinations[0], 5000)
            c.root.replicateBlock(file, path, destinations)
        return


    def exposed_test(self, message):
        print("Received Message: " + message)
        return "got ur message thx"


if __name__ == '__main__':
    from rpyc.utils.server import ThreadedServer
    t = ThreadedServer(DataNodeService, port=5000)
    t.start()
    #sendBlockReport(path)