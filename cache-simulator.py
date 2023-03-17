import sys
import json

# class for cache memory, which consists of caches described by the configuration file
class CacheMemory:
  def __init__(self):
    self.caches = []    # list of caches
    self.l1_cache_line_size = 0    # cache line size of l1 cache in bytes
    self.main_memory_accesses = 0    # number of main memory accesses
  
  # function to add cache to cache memory
  def add_cache(self, cache):
    # add cache to the end of the cache list
    self.caches.append(cache)
    # if this is the first cache added, set its cache line size as the l1 cache line size
    if len(self.caches) == 1:
      self.l1_cache_line_size = self.caches[0].line_size

  # function to lookup the required address in cache memory
  def lookup(self, address):
    # lookup the required address starting from l1 cache and return once found
    for cache in self.caches:
      if cache.lookup(address):
        return
    # the required address is not found, hence increment the number of main memory accesses
    self.main_memory_accesses += 1

# class for a direct mapped cache
class DirectMappedCache:
  def __init__(self, name, size, line_size):
    self.name = name    # cache name
    self.size = size    # cache size in bytes
    self.line_size = line_size    # cache line size in bytes
    self.line_count = size // line_size    # number of cache lines
    self.lines = [None for _ in range(self.line_count)]    # cache lines storing tags of memory blocks
    self.hits = 0    # number of cache hits
    self.misses = 0    # number of cache misses
  
  # function to lookup the required address in the current cache
  def lookup(self, address):
    # the first (n - a) bits of the n-bit address form the block id of the memory block, where 2^a = cache line size in bytes
    # the first (n - b) bits of the block id form the tag of the memory block, where 2^b = number of cache lines
    # the last b bits of the block id form the index of cache line which stores the memory block
    block_id = address // self.line_size
    tag = block_id // self.line_count
    index = block_id % self.line_count

    # check if the required tag is stored in the cache line of the concerend index
    if self.lines[index] == tag:
    # cache hit
      self.hits += 1
      return True
    else:
    # cache miss
      self.misses += 1
      # store the required tag to the cache line of the concerned index
      self.lines[index] = tag
      return False

# class for a fully associative cache
class FullyAssociativeCache:
  def __init__(self, name, size, line_size, replacement_policy):
    self.name = name    # cache name
    self.size = size    # cache size in bytes
    self.line_size = line_size    # cache line size in bytes
    self.replacement_policy = "rr" if replacement_policy == None else replacement_policy    # replacement policy, with round robin as default
    self.line_count = size // line_size    # number of cache lines
    self.lines = [None for _ in range(self.line_count)]    # cache lines storing tags of memory blocks, where the least recently used tag is stored at the beginning
    self.frequencies = [0 for _ in range(self.line_count)]    # access frequency for each tag in cache
    self.hits = 0    # number of cache hits
    self.misses = 0    # number of cache misses

  # function to lookup the required address in the current cache
  def lookup(self, address):
    # the first (n - a) bits of the n-bit address form the block id of the memory block, where 2^a = cache line size in bytes
    # the block id forms the tag of the memory block
    block_id = address // self.line_size
    tag = block_id

    # check if the required tag is stored in cache
    if tag in self.lines:
      # cache hit
      self.hits += 1
      # for LRU replacement, swap the required tag to the end of cache
      if self.replacement_policy == "lru":
        tag_index = self.lines.index(tag)
        self.lines.pop(tag_index)
        self.lines.append(tag)
      # for LFU replacement, increment the access frequency of the required tag
      elif self.replacement_policy == "lfu":
        tag_index = self.lines.index(tag)
        self.frequencies[tag_index] += 1
      return True
    else:
      # cache miss
      self.misses += 1
      # for round robin or LRU replacement, remove the first tag from cache, and store the required tag at the end
      if self.replacement_policy == "rr" or self.replacement_policy == "lru":
        self.lines.pop(0)
        self.lines.append(tag)
      # for LFU replacement, replace the least recently used tag with the required tag
      elif self.replacement_policy == "lfu":
        min_frequency = min(self.frequencies)
        min_index = self.frequencies.index(min_frequency)
        self.lines[min_index] = tag
        self.frequencies[min_index] = 1    # set access frequency of the required tag to 1
      return False

# class for a set associative cache
class SetAssociativeCache:
  def __init__(self, name, size, line_size, replacement_policy, associativity):
    self.name = name    # cache name
    self.size = size    # cache size in bytes
    self.line_size = line_size    # cache line size in bytes
    self.replacement_policy = "rr" if replacement_policy == None else replacement_policy    # replacement policy, with round robin as default
    self.associativity = associativity    # cache associativity
    self.line_count = size // line_size    # number of cache lines
    self.set_count = self.line_count // self.associativity    # number of cache sets
    self.sets = [[None for _ in range(self.associativity)] for _ in range(self.set_count)]    # sets of cache lines storing tags of memory blocks, where the least recently used tag is stored at the beginning of the set
    self.frequencies = [[0 for _ in range(self.associativity)] for _ in range(self.set_count)]    # access frequency for each tag in cache
    self.hits = 0    # number of cache hits
    self.misses = 0    # number of cache misses

  # function to lookup the required address in the current cache
  def lookup(self, address):
    # the first (n - a) bits of the n-bit address form the block id of the memory block, where 2^a = cache line size in bytes
    # the first (n - b) bits of the block id form the tag of the memory block, where 2^b = number of sets
    # the last b bits of the block id form the set index which stores the memory block
    block_id = address // self.line_size
    tag = block_id // self.set_count
    set = block_id % self.set_count
    
    # check if the required tag is stored in the concerend set
    if tag in self.sets[set]:
      # cache hit
      self.hits += 1
      # for LRU replacement, swap the required tag to the end of the set
      if self.replacement_policy == "lru":
        tag_index = self.sets[set].index(tag)
        self.sets[set].pop(tag_index)
        self.sets[set].append(tag)
      # for LFU replacement, increment the access frequency of the required tag
      elif self.replacement_policy == "lfu":
        tag_index = self.sets[set].index(tag)
        self.frequencies[set][tag_index] += 1
      return True
    else:
      # cache miss
      self.misses += 1
      # for round robin or LRU replacement, remove the first tag from the set, and store the required tag at the end of the set
      if self.replacement_policy == "rr" or self.replacement_policy == "lru":
        self.sets[set].pop(0)
        self.sets[set].append(tag)
      # for LFU replacement, replace the least recently used tag within the set with the required tag
      elif self.replacement_policy == "lfu":
        min_frequency = min(self.frequencies[set])
        min_index = self.frequencies[set].index(min_frequency)
        self.sets[set][min_index] = tag
        self.frequencies[set][min_index] = 1    # set access frequency of the required tag to 1
      return False

# main function
if __name__ == "__main__":
  argv = sys.argv
  if len(argv) != 3:
    print("usage: python3 cache-simulator.py <path-to-json-config-file> <path-to-trace-file>")
    sys.exit(1)

  # create cache memory
  cache_memory = CacheMemory()

  # read config file
  with open(argv[1]) as config_file:
    caches_data = json.load(config_file)["caches"]
    # add cache to cache memory according to their kinds
    for cache_data in caches_data:
      cache_kind = cache_data.get("kind")
      if cache_kind == "direct":
        cache_memory.add_cache(DirectMappedCache(cache_data.get("name"), cache_data.get("size"), cache_data.get("line_size")))
      elif cache_kind == "full":
        cache_memory.add_cache(FullyAssociativeCache(cache_data.get("name"), cache_data.get("size"), cache_data.get("line_size"), cache_data.get("replacement_policy")))
      elif cache_kind[1:4] == "way":
        cache_memory.add_cache(SetAssociativeCache(cache_data.get("name"), cache_data.get("size"), cache_data.get("line_size"), cache_data.get("replacement_policy"), int(cache_kind[0])))

  # read trace file
  with open(argv[2]) as trace_file:
    for instruction in trace_file:
      _, address, _, size = instruction.split()
      address = int(address, 16)    # starting address in decimal form
      size = int(size)    # size of memory operation in bytes
      offset = address % cache_memory.l1_cache_line_size    # offset of starting address in its memory block
      blocks_to_lookup = (offset + size - 1) // cache_memory.l1_cache_line_size + 1    # number of blocks to lookup for the memory operation
      # lookup each required address in cache memory
      for i in range(blocks_to_lookup):
        cache_memory.lookup(address + i * cache_memory.l1_cache_line_size)    # the next address to lookup = next memory block

  # output cache statistics
  caches_results = [{"name": cache.name, "hits": cache.hits, "misses": cache.misses} for cache in cache_memory.caches]
  results = {"main_memory_accesses": cache_memory.main_memory_accesses, "caches": caches_results}
  print(json.dumps(results, indent=2))