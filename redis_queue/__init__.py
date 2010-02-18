#   Copyright 2010 O'Reilly Media Inc.
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import redis

class Queue(object):
    """Implements the same interface as collections.dequeue, except for creation."""
    
    def __init__(self, redis, key):
        """Create a Queue backed by redis.
        
        Parameters:
        - redis: a Redis database object from redis.
        - key: The redis key to store the queue's backing list in."""
        self._redis = redis
        self.key = key
    
    def append(self, x):
        self._redis.push(self.key, x)
    
    def appendleft(self, x):
        self._redis.push(self.key, x, head=True)
    
    def clear(self):
        self._redis.delete(self.key)
    
    def extend(self, iterable):
        """Non-atomic. append each of the items from iterable in turn."""
        for item in iterable:
            self.append(item)
    
    def extendleft(self, iterable):
        """Non-atomic. appendleft each of the items from iterable in turn."""
        for item in iterable:
            self.appendleft(item)
    
    def pop(self):
        item = self._redis.pop(self.key, tail=True)
        if item is None:
            raise IndexError
        return item
    
    def popleft(self):
        item = self._redis.pop(self.key)
        if item is None:
            raise IndexError
        return item
    
    def remove(self, value):
        num_removed = self._redis.lrem(self.key, value)
        if num_removed == 0:
            raise ValueError()
    
    def rotate(self):
        """rotates the queue one step only."""
        self_redis.poppush(self.key, self.key)
        
    # Membership
    def __contains__(self, item):
        # This could stand to be a lot more efficient.
        # Why doesn't redis support this on the server side?
        members = self._redis.lrange(self.key, 0, -1)
        return item in members
    
    # Length
    def __len__(self):
        return self._redis.llen(self.key)
    
    # Subscript
    def __getitem__(self, key):
        item = self._redis.lindex(self.key, key)
        if item is None:
            raise IndexError
        return item
    
    def __setitem__(self, key, value):
        try:
            self._redis.lset(self.key, key, value)
        except redis.ResponseError, e:
            raise IndexError(e)
    
    # Iteration
    def __iter__(self):
        members = self._redis.lrange(self.key, 0, -1)
        return iter(members)

class ExclusiveQueue(Queue):
    """A queue that implements exclusivity (a given thing can only be in the
    queue once. This is not at all atomic; it pops something off then removes
    all other instances from the queue."""
    
    def pop(self):
        """pop and return the rightmost item in the queue, then delete all other
        instances of this item from the queue.
        
        While both of the operations used are atomic, this method itself is not."""
        item = super(ExclusiveQueue, self).pop()
        try:
            self.remove(item)
        except ValueError:
            pass
        return item
    
    def popleft(self):
        """pop and return the leftmost item in the queue, then delete all other
        instances of this item from the queue.
        
        While both of the operations used are atomic, this method itself is not."""
        item = super(ExclusiveQueue, self).popleft()
        try:
            self.remove(item)
        except ValueError:
            pass
        return item
