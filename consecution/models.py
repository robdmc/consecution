
import uuid
from django.db import models

TUP_HASH_BYTES = 20
NODE_HASH_BYTES = 20

"""
Started thinking about hashing system, but realized I need to finiis the code
for tuple trees first.  Here is where I left off

Still haven't decided if I want to track every tuple or just producer tuples.
In the case of tracking every tuple, bit might be cool to store the node
that generated it.  The way the node is stored is as follows.
Find a way to serialize consecutors.  Ideally as strings.  What this means
is that given proper modules on the path, I can take the serialized string
and create a consecutor ready to be wired up to a producer.

Now every node can store the sub-consecutor comprised of all itself and all
its child nodes simply by storing the sub-consecutor serialization.

Providing a way to hash the serialization then gives a good way to create
node ids.

What is cool here is that each time an item is created, it can check to see
if the node in which it is created already exists in the database.  If not
it can be created.



"""

def get_node_hash(obj):
    h = hashlib.sha512()
    h.update('7'.encode())
    d = h.hexdigest()
def new_hash(as_int=False, num_bytes):
    rand_int = random.getrandbits(8 * num_bytes)
    if as_int:
        return rand_int
    else
        return hash_int.to_bytes(num_bytes, sys.byteorder)


class StoredNode(models.Model):
    """
    Stores all information required to reconstruct a consecutor starting
    with and including a given node.
    Is identified by the has of the serialization.
    """
    # the sha1 has of the serialization
    hash_id = models.CharField(max_length=20, db_index=True)
    serialization = models.TextField()





class StoredItem(models.Model):
    node_hash = models.CharField(max_length=2 * NODE_HASH_BYTES + 3, db_index=True)
    ack_hash = models.CharField(max_length=2 * TUP_HASH_BYTES + 3, db_index=True)
    payload = models.BinaryField(null=True)
